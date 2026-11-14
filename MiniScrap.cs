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
    [Info("Mini Scrap", "Whispers88", "1.3.0")]
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

            // At the limit the player's oldest mini is removed to make room for the new one.
            [JsonProperty("Maximum minis per player at once (0 = unlimited)")]
            public int MaxMinis = 1;

            [JsonProperty("At the limit, remove the oldest mini even while someone is mounted on it")]
            public bool ReplaceOccupied = false;

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
                public string OldestInUse = "Your oldest minicopter cannot be replaced while someone is on it.";
                public string SpawnSuccess = "A minicopter has been spawned next to you!";
                public string SpawnReplaced = "A minicopter has been spawned next to you! Your oldest one was removed (limit {0}).";
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

        private StoredData _data = new StoredData();
        private bool _dataDirty;

        // Entities can only be looked up once the save has been loaded.
        private bool _serverReady;

        private string _permUse;

        #endregion Fields

        #region Hooks

        private void Init()
        {
            _permUse = $"{Name}.use";
            permission.RegisterPermission(_permUse, this);
            LoadData();
        }

        private void OnServerInitialized(bool initial)
        {
            // Net IDs start again with every new save, so minis recorded under another save cannot be matched against this one.
            string wipeId = SaveRestore.WipeId;
            if (_data.WipeId != wipeId)
            {
                _data.Minis.Clear();
                _data.WipeId = wipeId;
                _dataDirty = true;
            }

            _serverReady = true;
            PruneMinis();
        }

        private void OnServerSave()
        {
            PruneCooldowns();
            PruneMinis();
            SaveData();
        }

        private void Unload()
        {
            PruneCooldowns();
            SaveData();
        }

        #endregion Hooks

        #region Command

        [ChatCommand("mini")]
        private void cmdMinicopter(BasePlayer player, string command, string[] args)
        {
            var messages = config.messageSettings;

            // Tests run cheapest first. Nothing down to the scrap count queries the world, so a player who
            // cannot buy right now costs a few dictionary reads however often they ask.
            if (!permission.UserHasPermission(player.UserIDString, _permUse))
            {
                Reply(player, messages.NoPerms);
                return;
            }

            if (player.IsDead() || player.IsWounded() || player.IsSleeping() || player.isMounted || !player.IsOnGround())
            {
                Reply(player, messages.InvalidState);
                return;
            }

            ulong userId = player.userID;

            // At the limit the oldest mini makes way for the new one. How many have to go is worked out here,
            // while refusing is still cheap; they are only removed once the new mini is spawned and paid for.
            int maxMinis = config.MaxMinis;
            int toReplace = maxMinis > 0 ? CountMinis(userId) - maxMinis + 1 : 0;
            if (toReplace > 0 && !config.ReplaceOccupied && OldestMiniInUse(userId, toReplace))
            {
                Reply(player, messages.OldestInUse);
                return;
            }

            double now = UnixNow();
            if (_data.Cooldowns.TryGetValue(userId, out double endTime) && endTime > now)
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

            // From here on every test is a world query: water, then building privilege, then physics.
            if (player.IsSwimming())
            {
                Reply(player, messages.InvalidState);
                return;
            }

            if (!config.AllowSafeZone && player.InSafeZone())
            {
                Reply(player, messages.SafeZone);
                return;
            }

            if (player.IsBuildingBlocked())
            {
                Reply(player, messages.BuildingBlocked);
                return;
            }

            // Yaw only, so looking straight up or down still gives a usable direction.
            Quaternion yaw = Quaternion.Euler(0f, player.eyes.rotation.eulerAngles.y, 0f);
            Quaternion rotation = yaw * Quaternion.Euler(0f, config.Rotation, 0f);

            if (!TryGetSpawnPosition(player, toReplace, yaw * Vector3.forward, rotation, out Vector3 minicopterPos, out string error))
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
                int taken = player.inventory.Take(null, _scrap, scrapPrice);
                if (taken < scrapPrice)
                {
                    // The count was checked above, so this needs another plugin to answer the two calls differently.
                    // Either way a mini is never handed over for less than its price.
                    RefundScrap(player, taken);
                    minicopter.Kill();
                    PrintWarning($"Took {taken} of {scrapPrice} scrap from {player.UserIDString}; the purchase was cancelled and refunded");
                    Reply(player, messages.SpawnFailed);
                    return;
                }
            }

            int replaced = toReplace > 0 ? RemoveOldestMinis(userId, toReplace) : 0;
            TrackMini(userId, minicopter);

            if (config.MiniCooldown > 0)
            {
                _data.Cooldowns[userId] = now + config.MiniCooldown;
                _dataDirty = true;
            }

            if (config.Fuel > 0)
            {
                minicopter.GetFuelSystem()?.AddFuel(config.Fuel);
            }

            Reply(player, replaced > 0 ? string.Format(messages.SpawnReplaced, maxMinis) : messages.SpawnSuccess);
        }

        private void RefundScrap(BasePlayer player, int amount)
        {
            if (amount <= 0)
            {
                return;
            }

            Item item = ItemManager.CreateByItemID(_scrap, amount);
            if (item != null)
            {
                player.GiveItem(item);
            }
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

        private bool TryGetSpawnPosition(BasePlayer player, int toReplace, Vector3 forward, Quaternion rotation, out Vector3 spawnPos, out string error)
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

            // The probe can land on top of a low or half wall, which is not somewhere to park.
            BuildingBlock surfaceBlock = ground.collider.ToBaseEntity() as BuildingBlock;
            if (surfaceBlock != null && surfaceBlock.ShortPrefabName.Contains("wall"))
            {
                error = messages.NotNearBuildingBlock;
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

            if (!HasClearance(player, toReplace, ground.point, rotation))
            {
                return false;
            }

            if (CheckForBuildingBlocks(spawnPos, ground.point.y))
            {
                error = messages.NotNearBuildingBlock;
                return false;
            }

            // The player's own position was checked earlier; this covers the spot the mini will occupy.
            // It is the most expensive test here, so it runs last.
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
        // The buyer does not count, and neither do the minis this purchase is about to replace: they are gone
        // before the next physics step, so a replacement can be bought on the very spot where the old mini stands.
        private bool HasClearance(BasePlayer player, int toReplace, Vector3 groundPoint, Quaternion rotation)
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

                BaseEntity entity = collider.ToBaseEntity();
                if (entity == player)
                {
                    continue;
                }

                if (toReplace > 0 && IsOldestMini(entity, player.userID, toReplace))
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

        #region Mini limit

        // A player's minis are remembered by net ID, oldest first, and looked up when needed. Nothing is
        // subscribed to OnEntitySpawned or OnEntityKill, so the limit costs nothing while nobody is buying.
        // A mini that is gone for any reason (shot down, decayed, removed by an admin) simply stops being found.

        private void TrackMini(ulong userId, Minicopter minicopter)
        {
            if (minicopter.net == null)
            {
                return;
            }

            if (!_data.Minis.TryGetValue(userId, out List<ulong> ids) || ids == null)
            {
                ids = new List<ulong>();
                _data.Minis[userId] = ids;
            }

            ids.Add(minicopter.net.ID.Value);
            _dataDirty = true;
        }

        // Forgets the player's minis that no longer exist and returns how many are left.
        private int CountMinis(ulong userId)
        {
            if (!_data.Minis.TryGetValue(userId, out List<ulong> ids))
            {
                return 0;
            }

            if (ids != null && RemoveMissingMinis(userId, ids))
            {
                _dataDirty = true;
            }

            if (ids == null || ids.Count == 0)
            {
                _data.Minis.Remove(userId);
                _dataDirty = true;
                return 0;
            }

            return ids.Count;
        }

        // True if any of the player's oldest minis (as many as given) has someone mounted on it.
        private bool OldestMiniInUse(ulong userId, int count)
        {
            if (!_data.Minis.TryGetValue(userId, out List<ulong> ids) || ids == null)
            {
                return false;
            }

            for (int i = 0; i < count && i < ids.Count; i++)
            {
                Minicopter minicopter = FindMini(userId, ids[i]);
                if (minicopter != null && minicopter.AnyMounted())
                {
                    return true;
                }
            }

            return false;
        }

        // True if the entity is, or is attached to, one of the player's oldest minis (as many as given).
        private bool IsOldestMini(BaseEntity entity, ulong userId, int count)
        {
            if (!_data.Minis.TryGetValue(userId, out List<ulong> ids) || ids == null)
            {
                return false;
            }

            // Seats and the fuel tank are entities of their own, parented to the mini.
            while (entity != null)
            {
                Minicopter minicopter = entity as Minicopter;
                if (minicopter != null)
                {
                    if (minicopter.net == null)
                    {
                        return false;
                    }

                    int index = ids.IndexOf(minicopter.net.ID.Value);
                    return index >= 0 && index < count;
                }

                entity = entity.GetParentEntity();
            }

            return false;
        }

        // Removes the player's oldest minis (as many as given) from the world. Returns how many went.
        private int RemoveOldestMinis(ulong userId, int count)
        {
            if (!_data.Minis.TryGetValue(userId, out List<ulong> ids) || ids == null)
            {
                return 0;
            }

            int removed = 0;
            int index = 0;
            while (count > 0 && index < ids.Count)
            {
                count--;

                Minicopter minicopter = FindMini(userId, ids[index]);
                if (minicopter != null)
                {
                    minicopter.Kill();
                    if (!minicopter.IsDestroyed)
                    {
                        // Another plugin refused the removal (OnEntityKill). It stays on record and still counts.
                        PrintWarning($"Could not remove minicopter {ids[index]} of {userId}: another plugin blocked it");
                        index++;
                        continue;
                    }

                    removed++;
                }

                ids.RemoveAt(index);
                _dataDirty = true;
            }

            return removed;
        }

        private static bool RemoveMissingMinis(ulong userId, List<ulong> ids)
        {
            bool removed = false;
            for (int i = ids.Count - 1; i >= 0; i--)
            {
                if (FindMini(userId, ids[i]) == null)
                {
                    ids.RemoveAt(i);
                    removed = true;
                }
            }

            return removed;
        }

        // The player's mini with this net ID, or null if it is gone. Gone covers destroyed, dead (out of health,
        // by decay or damage, even if something delayed its removal) and handed to another owner.
        private static Minicopter FindMini(ulong userId, ulong netId)
        {
            Minicopter minicopter = BaseNetworkable.serverEntities.Find(new NetworkableId(netId)) as Minicopter;
            if (minicopter == null || minicopter.IsDestroyed || minicopter.IsDead())
            {
                return null;
            }

            // Never touch a mini that now carries somebody else's owner ID, whatever the record says.
            if (minicopter.OwnerID != 0 && minicopter.OwnerID != userId)
            {
                return null;
            }

            return minicopter;
        }

        // Keeps the data file to minis that still exist. One dictionary read per remembered mini.
        private void PruneMinis()
        {
            if (!_serverReady || _data.Minis.Count == 0)
            {
                return;
            }

            List<ulong> empty = Pool.Get<List<ulong>>();
            try
            {
                foreach (var entry in _data.Minis)
                {
                    if (entry.Value != null && RemoveMissingMinis(entry.Key, entry.Value))
                    {
                        _dataDirty = true;
                    }

                    if (entry.Value == null || entry.Value.Count == 0)
                    {
                        empty.Add(entry.Key);
                    }
                }

                foreach (var id in empty)
                {
                    _data.Minis.Remove(id);
                }

                if (empty.Count > 0)
                {
                    _dataDirty = true;
                }
            }
            finally
            {
                Pool.FreeUnmanaged(ref empty);
            }
        }

        #endregion Mini limit

        #region Data

        private class StoredData
        {
            // The save these records belong to. Net IDs are only unique within one save.
            public string WipeId;

            // Steam ID -> UTC unix time (seconds) at which the player may buy again.
            public Dictionary<ulong, double> Cooldowns = new Dictionary<ulong, double>();

            // Steam ID -> net IDs of the minis the player bought, oldest first.
            public Dictionary<ulong, List<ulong>> Minis = new Dictionary<ulong, List<ulong>>();
        }

        private static double UnixNow() => (DateTime.UtcNow - UnixEpoch).TotalSeconds;

        private void LoadData()
        {
            try
            {
                _data = Interface.Oxide.DataFileSystem.ReadObject<StoredData>(Name);
            }
            catch
            {
                PrintWarning($"Data file {Name}.json is invalid; cooldowns and mini counts reset");
                _data = null;
            }

            if (_data == null)
            {
                _data = new StoredData();
            }

            if (_data.Cooldowns == null)
            {
                _data.Cooldowns = new Dictionary<ulong, double>();
            }

            if (_data.Minis == null)
            {
                _data.Minis = new Dictionary<ulong, List<ulong>>();
            }
        }

        private void SaveData()
        {
            if (!_dataDirty)
            {
                return;
            }

            Interface.Oxide.DataFileSystem.WriteObject(Name, _data);
            _dataDirty = false;
        }

        private void PruneCooldowns()
        {
            if (_data.Cooldowns.Count == 0)
            {
                return;
            }

            double now = UnixNow();
            List<ulong> expired = Pool.Get<List<ulong>>();
            try
            {
                foreach (var entry in _data.Cooldowns)
                {
                    if (entry.Value <= now)
                    {
                        expired.Add(entry.Key);
                    }
                }

                foreach (var id in expired)
                {
                    _data.Cooldowns.Remove(id);
                }

                if (expired.Count > 0)
                {
                    _dataDirty = true;
                }
            }
            finally
            {
                Pool.FreeUnmanaged(ref expired);
            }
        }

        #endregion Data
    }
}
