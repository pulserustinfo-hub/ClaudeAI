using System;
using Newtonsoft.Json;
using Oxide.Core;
using Oxide.Core.Configuration;
using Oxide.Core.Plugins;
using Rust;
using UnityEngine;
using System.Collections.Generic;
using System.Linq;
using Facepunch;

namespace Oxide.Plugins
{
    [Info("Mini Scrap", "Whispers88", "1.0.2")]
    [Description("Spawns a minicopter next to a player if they have enough scrap.")]
    class MiniScrap : RustPlugin
    {
        #region Configuration

        private Configuration config;

        public class Configuration
        {
            [JsonProperty("Mini Price (Scrap)")]
            public int ScrapPrice = 750;

            [JsonProperty("Mini Rotation (Degrees)")]
            public float Rotation = 90f;

            [JsonProperty("Mini Distance from Player")]
            public float DistfromPlayer = 3f;

            [JsonProperty("Mini Up Displacement")]
            public float UpDisplacement = 1.5f;

            [JsonProperty("Mini Fuel")]
            public int Fuel = 100;

            [JsonProperty("Mini cooldown time")]
            public float MiniCooldown = 60;

            [JsonProperty("Chat ID")]
            public ulong ChatID = 76561198152495837;

            [JsonProperty("Minimum distance from stability entity (doors, walls etc)")]
            public float BuildingBlockCheckDist = 2;

            [JsonProperty("Message Settings")]
            public MessageSettings messageSettings = new MessageSettings();
            public class MessageSettings
            {
                public string NotInside = "You cannot spawn a minicopter inside.";
                public string CannotSee = "Spawn position is not clear.";
                public string NotNearBuildingBlock = "You cannot spawn a minicopter near a building block.";
                public string NotEnoughScrap = "You need {0} scrap to buy a minicopter";
                public string CooldownMsg = "You must wait {0} more minutes before spawning another mini.";
                public string SpawnSuccess = "A minicopter has been spawned next to you!";
                public string NoPerms = "You do not have permission to use this command.";
                public string BuildingBlocked = "Your in a building blocked zone";
            }

            //[JsonProperty("ScrapHeli Price (Scrap)")]
            //public int ScrapHeliPrice = 1500;

            //[JsonProperty("ScrapHeli Rotation (Degrees)")]
            //public float ScrapHeliRotation = 90f;

            //[JsonProperty("ScrapHeli Distance from Player")]
            //public float ScrapHeliDistfromPlayer = 10f;

            //[JsonProperty("ScrapHeli Up Displacement")]
            //public float ScrapHeliUpDisplacement = 2f;

            //[JsonProperty("ScrapHeli Fuel")]
            //public int ScrapHeliFuel = 100;

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

                if (!config.ToDictionary().Keys.SequenceEqual(Config.ToDictionary(x => x.Key, x => x.Value).Keys))
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

        private void Init()
        {
            LoadConfig();
            permission.RegisterPermission($"{this.Name}.use", this);
        }

        private const string _miniprefab = "assets/content/vehicles/minicopter/minicopter.entity.prefab";
        private const string _scrapheli = "assets/content/vehicles/scrap heli carrier/scraptransporthelicopter.prefab";
        private static int _scrap = -932201673;

        [ChatCommand("mini")]
        private void cmdMinicopter(BasePlayer player, string command, string[] args)
        {
            if (!CanSpawnMinicopter(player))
            {
                return;
            }

            var playerPos = player.transform.position;
            var minicopterPos = playerPos + (player.eyes.BodyForward().XZ3D().normalized * config.DistfromPlayer) + Vector3.up * config.UpDisplacement;
            if (CheckInside(minicopterPos))
            {
                Player.Message(player, config.messageSettings.NotInside, config.ChatID);
                return;
            }

            if (CheckForBuildingBlocks(minicopterPos))
            {
                Player.Message(player, config.messageSettings.NotNearBuildingBlock, config.ChatID);
                return;
            }

            if (ViewObstructed(playerPos, minicopterPos))
            {
                Player.Message(player, config.messageSettings.CannotSee, config.ChatID);
                return;
            }

            int scrapPrice = config.ScrapPrice;
            if (player.inventory.GetAmount(_scrap) < scrapPrice)
            {
                Player.Message(player, string.Format(config.messageSettings.NotEnoughScrap, scrapPrice), config.ChatID);
                return;
            }

            if (Cooldown.TryGetValue(player.userID, out var endTime) && endTime > Time.time)
            {
                Player.Message(player, string.Format(config.messageSettings.CooldownMsg, Mathf.RoundToInt((endTime - Time.time) / 60)), config.ChatID);
                return;
            }
            Cooldown[player.userID] = Time.time + config.MiniCooldown;

            player.inventory.Take(null, _scrap, scrapPrice);
            Vector3 forward = player.eyes.rotation * Vector3.forward;
            forward.y = 0;
            Quaternion additionalRotation = Quaternion.Euler(0, config.Rotation, 0); // 90 degrees rotation around the Y-axis

            Minicopter minicopter = (Minicopter)GameManager.server.CreateEntity(_miniprefab, minicopterPos, Quaternion.LookRotation(forward) * additionalRotation);
            minicopter.Spawn();

            minicopter.GetFuelSystem().AddFuel(config.Fuel);

            Player.Message(player, config.messageSettings.SpawnSuccess, config.ChatID);
        }

        Dictionary<ulong, float> Cooldown = new Dictionary<ulong, float>();
        private bool CanSpawnMinicopter(BasePlayer player)
        {
            if (!permission.UserHasPermission(player.UserIDString, $"{this.Name}.use"))
            {
                Player.Message(player, config.messageSettings.NoPerms, config.ChatID);
                return false;
            }
            if (player.IsBuildingBlocked())
            {
                Player.Message(player, config.messageSettings.BuildingBlocked, config.ChatID);
                return false;
            }            
            return true;
        }

        void OnServerSave()
        {
            ServerMgr.Instance.Invoke(() => ClearCooldowns(), 10);
        }

        private void ClearCooldowns()
        {
            List<ulong> removes = Pool.Get<List<ulong>>();
            try
            {
                foreach (var id in Cooldown)
                    if (id.Value <= Time.time)
                        removes.Add(id.Key);

                foreach (var remove in removes)
                    Cooldown.Remove(remove);
            }
            finally
            {
                Pool.FreeUnmanaged(ref removes);
            }
        }

        public static bool CheckInside(Vector3 checkPosition)
        {
            return Physics.Raycast(checkPosition, Vector3.up, 20f, Layers.Mask.Construction | Layers.Mask.Deployed | Layers.Mask.Terrain);
        }

        public static bool ViewObstructed(Vector3 from, Vector3 to)
        {
            var direction = (to - from).normalized;
            var distance = Vector3.Distance(from, to);
            return Physics.Raycast(from, direction, distance, Layers.Mask.Construction | Layers.Mask.Deployed | Layers.Mask.Terrain);
        }

        public bool CheckForBuildingBlocks(Vector3 pos)
        {
            var nearby = FindEntitiesOfType<StabilityEntity>(pos, config.BuildingBlockCheckDist);
            try
            {
                foreach (var entity in nearby)
                {
                    if (entity is BuildingBlock)
                    {
                        var entityPos = entity.transform.position;
                        if ((entity.ShortPrefabName.Contains("foundation") || entity.ShortPrefabName.Contains("floor")) && entityPos.y < pos.y) continue;
                        if (pos.y - entityPos.y > 1) continue;
                    }                    
                    
                    return true;
                }

                return false;
            }
            finally
            {
                Pool.FreeUnmanaged(ref nearby);
            }
        }

        private static List<T> FindEntitiesOfType<T>(Vector3 pos, float radius, int m = -1) where T : BaseEntity
        {
            int hits = Physics.OverlapSphereNonAlloc(pos, radius, Vis.colBuffer, m, QueryTriggerInteraction.Collide);
            List<T> entities = Pool.Get<List<T>>();
            for (int i = 0; i < hits; i++)
            {
                var entity = Vis.colBuffer[i]?.ToBaseEntity();
                if (entity is T) entities.Add(entity as T);
                Vis.colBuffer[i] = null;
            }
            return entities;
        }
    }
}