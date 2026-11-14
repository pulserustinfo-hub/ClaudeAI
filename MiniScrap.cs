using System;
using System.Collections.Generic;
using System.Linq;
using Facepunch;
using Newtonsoft.Json;
using Oxide.Core;
using Rust;
using UnityEngine;

namespace Oxide.Plugins
{
    [Info("Mini Scrap", "Whispers88", "1.1.0")]
    [Description("Spawns a minicopter next to a player if they have enough scrap.")]
    class MiniScrap : RustPlugin
    {
        #region Configuration

        private Configuration config;

        // Default cooldown text shipped up to 1.0.2. {0} used to be whole minutes; it is now a formatted duration.
        private const string LegacyCooldownMsg = "You must wait {0} more minutes before spawning another mini.";

        public class Configuration
        {
            [JsonProperty("Mini Price (Scrap)")]
            public int ScrapPrice = 750;

            [JsonProperty("Mini Rotation (Degrees)")]
            public float Rotation = 90f;

            [JsonProperty("Mini Distance from Player")]
            public float DistfromPlayer = 3f;

            // Height above the ground at the spawn point (not above the player's feet).
            [JsonProperty("Mini Up Displacement")]
            public float UpDisplacement = 1.5f;

            [JsonProperty("Mini Fuel")]
            public int Fuel = 100;

            // Seconds.
            [JsonProperty("Mini cooldown time")]
            public float MiniCooldown = 60;

            [JsonProperty("Chat ID")]
            public ulong ChatID = 76561198152495837;

            [JsonProperty("Minimum distance from stability entity (doors, walls etc)")]
            public float BuildingBlockCheckDist = 2;

            [JsonProperty("Clear space required around the mini (metres, 0 = no check)")]
            public float ClearanceRadius = 2f;

            [JsonProperty("Allow spawning in safe zones")]
            public bool AllowSafeZone = false;

            [JsonProperty("Set the buyer as owner of the mini")]
            public bool SetOwner = true;

            [JsonProperty("Message Settings")]
            public MessageSettings messageSettings = new MessageSettings();
            public class MessageSettings
            {
                public string NotInside = "You cannot spawn a minicopter inside.";
                public string CannotSee = "Spawn position is not clear.";
                public string NotNearBuildingBlock = "You cannot spawn a minicopter near a building block.";
                public string NotEnoughScrap = "You need {0} scrap to buy a minicopter";
                public string CooldownMsg = "You must wait {0} before spawning another mini.";
                public string SpawnSuccess = "A minicopter has been spawned next to you!";
                public string NoPerms = "You do not have permission to use this command.";
                public string BuildingBlocked = "You're in a building blocked zone";
                public string InvalidState = "You cannot spawn a minicopter while mounted, swimming, airborne or wounded.";
                public string SafeZone = "You cannot spawn a minicopter in a safe zone.";
                public string SpawnFailed = "The minicopter could not be spawned. You have not been charged.";
            }

            public string ToJson() => JsonConvert.SerializeObject(this);

            public Dictionary<string, object> ToDictionary() => JsonConvert.DeserializeObject<Dictionary<string, object>>(ToJson());
        }

        protected override void LoadDefaultConfig() => config = new Configuration();

        protected override void LoadConfig()
        {
            base.LoadConfig();
            try
            {
                config = Config.ReadObject<Configuration>();
                if (config == null)
                {
                    throw new JsonException();
                }

                bool changed = false;

                if (config.messageSettings == null)
                {
                    config.messageSettings = new Configuration.MessageSettings();
                    changed = true;
                }

                if (config.messageSettings.CooldownMsg == LegacyCooldownMsg)
                {
                    config.messageSettings.CooldownMsg = new Configuration.MessageSettings().CooldownMsg;
                    changed = true;
                }

                if (!config.ToDictionary().Keys.SequenceEqual(Config.ToDictionary(x => x.Key, x => x.Value).Keys))
                {
                    changed = true;
                }

                if (changed)
                {
                    Puts("Configuration appears to be outdated; updating and saving");
                    SaveConfig();
                }
            }
            catch
            {
                Puts($"Configuration file {Name}.json is invalid; using defaults");
                LoadDefaultConfig();
            }
        }

        protected override void SaveConfig()
        {
            Puts($"Configuration changes saved to {Name}.json");
            Config.WriteObject(config, true);
        }

        #endregion Configuration

        #region Fields

        private const string _miniprefab = "assets/content/vehicles/minicopter/minicopter.entity.prefab";
        private const int _scrap = -932201673;

        // How far above / below the player's feet the ground at the spawn point may be.
        private const float GroundProbeUp = 2f;
        private const float GroundProbeDown = 3f;

        // The clearance volume starts this far above the ground so small bumps do not count as obstacles.
        private const float ClearanceGap = 0.4f;
        private const float MiniHeight = 2.5f;

        // A building block whose top is no higher than this above the spawn surface is treated as being underneath the mini.
        private const float BelowSurfaceTolerance = 0.25f;

        // Rocks, cliffs and monument buildings are on the World layer.
        private static readonly int GroundMask = Layers.Mask.Terrain | Layers.Mask.World | Layers.Mask.Construction;
        private static readonly int SolidMask = GroundMask | Layers.Mask.Deployed;
        private static readonly int ClearanceMask = Layers.Mask.World | Layers.Mask.Construction | Layers.Mask.Deployed
            | Layers.Mask.Tree | Layers.Mask.Vehicle_World | Layers.Mask.Vehicle_Large | Layers.Mask.Vehicle_Detailed
            | Layers.Mask.Player_Server | Layers.Mask.AI;

        private static readonly DateTime UnixEpoch = new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc);

        // Steam ID -> UTC unix time (seconds) at which the player may buy again. Saved to the data file.
        private Dictionary<ulong, double> _cooldowns = new Dictionary<ulong, double>();
        private bool _cooldownsDirty;

        private string PermUse => $"{Name}.use";

        #endregion Fields

        #region Hooks

        private void Init()
        {
            permission.RegisterPermission(PermUse, this);
            LoadCooldowns();
        }

        private void OnServerSave() => SaveCooldowns();

        private void Unload() => SaveCooldowns();

        #endregion Hooks

        #region Command

        [ChatCommand("mini")]
        private void cmdMinicopter(BasePlayer player, string command, string[] args)
        {
            var messages = config.messageSettings;

            if (!CanSpawnMinicopter(player))
            {
                return;
            }

            ulong userId = player.userID;
            double now = UnixNow();
            if (_cooldowns.TryGetValue(userId, out double endTime) && endTime > now)
            {
                Reply(player, string.Format(messages.CooldownMsg, FormatDuration(endTime - now)));
                return;
            }

            int scrapPrice = config.ScrapPrice;
            if (scrapPrice > 0 && player.inventory.GetAmount(_scrap) < scrapPrice)
            {
                Reply(player, string.Format(messages.NotEnoughScrap, scrapPrice));
                return;
            }

            // Yaw only, so looking straight up or down still gives a usable direction.
            Quaternion yaw = Quaternion.Euler(0f, player.eyes.rotation.eulerAngles.y, 0f);
            Quaternion rotation = yaw * Quaternion.Euler(0f, config.Rotation, 0f);

            if (!TryGetSpawnPosition(player, yaw * Vector3.forward, rotation, out Vector3 minicopterPos, out string error))
            {
                Reply(player, error);
                return;
            }

            // Spawn first and charge afterwards, so a failed spawn never costs the player anything.
            BaseEntity entity = GameManager.server.CreateEntity(_miniprefab, minicopterPos, rotation);
            Minicopter minicopter = entity as Minicopter;
            if (minicopter == null)
            {
                if (entity != null)
                {
                    UnityEngine.Object.Destroy(entity.gameObject);
                }

                PrintWarning($"Could not create a minicopter from '{_miniprefab}'");
                Reply(player, messages.SpawnFailed);
                return;
            }

            if (config.SetOwner)
            {
                minicopter.OwnerID = userId;
            }

            minicopter.Spawn();

            // Another plugin (an entity limiter, for example) may remove the mini as it spawns.
            if (minicopter == null || minicopter.IsDestroyed)
            {
                Reply(player, messages.SpawnFailed);
                return;
            }

            if (scrapPrice > 0)
            {
                player.inventory.Take(null, _scrap, scrapPrice);
            }

            if (config.MiniCooldown > 0)
            {
                _cooldowns[userId] = now + config.MiniCooldown;
                _cooldownsDirty = true;
            }

            if (config.Fuel > 0)
            {
                minicopter.GetFuelSystem()?.AddFuel(config.Fuel);
            }

            Reply(player, messages.SpawnSuccess);
        }

        private bool CanSpawnMinicopter(BasePlayer player)
        {
            var messages = config.messageSettings;

            if (!permission.UserHasPermission(player.UserIDString, PermUse))
            {
                Reply(player, messages.NoPerms);
                return false;
            }

            if (player.IsDead() || player.IsWounded() || player.IsSleeping() || player.isMounted || player.IsSwimming() || !player.IsOnGround())
            {
                Reply(player, messages.InvalidState);
                return false;
            }

            if (!config.AllowSafeZone && player.InSafeZone())
            {
                Reply(player, messages.SafeZone);
                return false;
            }

            if (player.IsBuildingBlocked())
            {
                Reply(player, messages.BuildingBlocked);
                return false;
            }

            return true;
        }

        private void Reply(BasePlayer player, string message) => Player.Message(player, message, config.ChatID);

        private static string FormatDuration(double seconds)
        {
            int total = Math.Max(1, (int)Math.Ceiling(seconds));
            if (total < 60)
            {
                return $"{total}s";
            }

            if (total < 3600)
            {
                int secs = total % 60;
                return secs == 0 ? $"{total / 60}m" : $"{total / 60}m {secs}s";
            }

            int mins = total % 3600 / 60;
            return mins == 0 ? $"{total / 3600}h" : $"{total / 3600}h {mins}m";
        }

        #endregion Command

        #region Spawn position

        private bool TryGetSpawnPosition(BasePlayer player, Vector3 forward, Quaternion rotation, out Vector3 spawnPos, out string error)
        {
            var messages = config.messageSettings;
            spawnPos = Vector3.zero;
            error = messages.CannotSee;

            Vector3 target = player.transform.position + forward * config.DistfromPlayer;

            // Put the mini on whatever is under the spawn point instead of at the player's own height.
            if (!Physics.Raycast(target + Vector3.up * GroundProbeUp, Vector3.down, out RaycastHit ground,
                    GroundProbeUp + GroundProbeDown, GroundMask, QueryTriggerInteraction.Ignore))
            {
                return false;
            }

            spawnPos = ground.point + Vector3.up * config.UpDisplacement;

            // From the eyes, so a rock or wall between the player and the spawn point is always crossed from its outside.
            if (ViewObstructed(player.eyes.position, spawnPos))
            {
                return false;
            }

            if (CheckInside(spawnPos))
            {
                error = messages.NotInside;
                return false;
            }

            if (!HasClearance(player, ground.point, rotation))
            {
                return false;
            }

            if (CheckForBuildingBlocks(spawnPos, ground.point.y))
            {
                error = messages.NotNearBuildingBlock;
                return false;
            }

            // The player's own position was checked earlier; this covers the spot the mini will occupy.
            float halfWidth = Mathf.Max(config.ClearanceRadius, 1f);
            Bounds miniBounds = new Bounds(new Vector3(0f, MiniHeight * 0.5f, 0f), new Vector3(halfWidth * 2f, MiniHeight, halfWidth * 2f));
            if (player.IsBuildingBlocked(spawnPos, rotation, miniBounds))
            {
                error = messages.BuildingBlocked;
                return false;
            }

            return true;
        }

        public static bool CheckInside(Vector3 checkPosition)
        {
            return Physics.Raycast(checkPosition, Vector3.up, 20f, SolidMask, QueryTriggerInteraction.Ignore);
        }

        public static bool ViewObstructed(Vector3 from, Vector3 to)
        {
            var direction = (to - from).normalized;
            var distance = Vector3.Distance(from, to);
            return Physics.Raycast(from, direction, distance, SolidMask, QueryTriggerInteraction.Ignore);
        }

        // True if nothing solid (rocks, walls, deployables, trees, vehicles, other players, animals) overlaps the space the mini needs.
        private bool HasClearance(BasePlayer player, Vector3 groundPoint, Quaternion rotation)
        {
            float radius = config.ClearanceRadius;
            if (radius <= 0f)
            {
                return true;
            }

            float halfHeight = Mathf.Max(config.UpDisplacement + MiniHeight - ClearanceGap, 1f) * 0.5f;
            Vector3 center = groundPoint + Vector3.up * (ClearanceGap + halfHeight);

            int hits = Physics.OverlapBoxNonAlloc(center, new Vector3(radius, halfHeight, radius), Vis.colBuffer, rotation, ClearanceMask, QueryTriggerInteraction.Ignore);
            bool clear = true;
            for (int i = 0; i < hits; i++)
            {
                Collider collider = Vis.colBuffer[i];
                Vis.colBuffer[i] = null;
                if (!clear || collider == null)
                {
                    continue;
                }

                if (collider.ToBaseEntity() == player)
                {
                    continue;
                }

                clear = false;
            }

            return clear;
        }

        public bool CheckForBuildingBlocks(Vector3 pos, float surfaceY)
        {
            float radius = config.BuildingBlockCheckDist;
            if (radius <= 0f)
            {
                return false;
            }

            int hits = Physics.OverlapSphereNonAlloc(pos, radius, Vis.colBuffer, -1, QueryTriggerInteraction.Ignore);
            bool found = false;
            for (int i = 0; i < hits; i++)
            {
                Collider collider = Vis.colBuffer[i];
                Vis.colBuffer[i] = null;
                if (found || collider == null)
                {
                    continue;
                }

                BaseEntity entity = collider.ToBaseEntity();
                if (!(entity is StabilityEntity))
                {
                    continue;
                }

                // Blocks wholly underneath the surface the mini stands on (the floor or foundation itself,
                // walls of the storey below) are not in the way. Anything rising above that surface is.
                if (entity is BuildingBlock && collider.bounds.max.y <= surfaceY + BelowSurfaceTolerance)
                {
                    continue;
                }

                found = true;
            }

            return found;
        }

        #endregion Spawn position

        #region Cooldowns

        private static double UnixNow() => (DateTime.UtcNow - UnixEpoch).TotalSeconds;

        private void LoadCooldowns()
        {
            try
            {
                _cooldowns = Interface.Oxide.DataFileSystem.ReadObject<Dictionary<ulong, double>>(Name);
            }
            catch
            {
                PrintWarning($"Data file {Name}.json is invalid; cooldowns reset");
                _cooldowns = null;
            }

            if (_cooldowns == null)
            {
                _cooldowns = new Dictionary<ulong, double>();
            }

            PruneCooldowns();
        }

        private void SaveCooldowns()
        {
            PruneCooldowns();
            if (!_cooldownsDirty)
            {
                return;
            }

            Interface.Oxide.DataFileSystem.WriteObject(Name, _cooldowns);
            _cooldownsDirty = false;
        }

        private void PruneCooldowns()
        {
            if (_cooldowns.Count == 0)
            {
                return;
            }

            double now = UnixNow();
            List<ulong> expired = Pool.Get<List<ulong>>();
            try
            {
                foreach (var entry in _cooldowns)
                {
                    if (entry.Value <= now)
                    {
                        expired.Add(entry.Key);
                    }
                }

                foreach (var id in expired)
                {
                    _cooldowns.Remove(id);
                }

                if (expired.Count > 0)
                {
                    _cooldownsDirty = true;
                }
            }
            finally
            {
                Pool.FreeUnmanaged(ref expired);
            }
        }

        #endregion Cooldowns
    }
}
