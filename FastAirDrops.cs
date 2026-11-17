using Newtonsoft.Json;
using Newtonsoft.Json.Serialization;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace Oxide.Plugins
{
    [Info("FastAirDrops", "Whispers88", "1.1.2")]
    [Description("FastAirDrops")]
    public class FastAirDrops : CovalencePlugin
    {
        #region Configuration

        private Configuration config;

        public class Configuration
        {
            [JsonProperty("Speed up plane percentage (0-100)")]
            public float SpeedUpPlanePercentage = 95f;

            [JsonProperty("Supply drop speed (min 0.5 fastest, default 3.0)")]
            public float DropDrag = 0.6f;

            [JsonProperty("Smoke duration [0 = off][Max: 210]")]
            public float SmokeDuration = 0;

            [JsonProperty("Airdrop despawn time in seconds (0 = disabled)")]
            public float DespawnTime = 0f;

            [JsonProperty("Supply Cooldown Time (seconds) (0 = disabled)")]
            public float SupplyCooldownTime = 300;

            [JsonProperty("Maximum airdrops alive at once per team (0 = unlimited)")]
            public int SupplyMaxAlive = 5;

            public string ToJson() => JsonConvert.SerializeObject(this);

            public Dictionary<string, object> ToDictionary() =>
                JsonConvert.DeserializeObject<Dictionary<string, object>>(ToJson());
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
                    LogWarning("Configuration appears to be outdated; updating and saving");
                    SaveConfig();
                }
            }
            catch
            {
                LogWarning($"Configuration file {Name}.json is invalid; using defaults");
                LoadDefaultConfig();
            }
        }

        protected override void SaveConfig()
        {
            LogWarning($"Configuration changes saved to {Name}.json");
            Config.WriteObject(config, true);
        }

        #endregion Configuration

        #region Localization

        private const string MsgCooldown = "Cooldown";
        private const string MsgMaxAlive = "MaxAlive";

        protected override void LoadDefaultMessages()
        {
            lang.RegisterMessages(new Dictionary<string, string>
            {
                [MsgCooldown] = "You must wait {0}s before throwing another supply signal.",
                [MsgMaxAlive] = "You can't have more than {0} airdrop(s) active at once.\nWait for one to be looted or to despawn before throwing another."
            }, this);
        }

        private string Msg(string key, BasePlayer player, params object[] args) =>
            string.Format(lang.GetMessage(key, this, player.UserIDString), args);

        #endregion Localization

        private readonly Dictionary<BaseEntity, ulong> airdropOwners = new Dictionary<BaseEntity, ulong>();

        private readonly Dictionary<ulong, float> teamCooldownUntil = new Dictionary<ulong, float>();

        private void OnAirdrop(CargoPlane instance, Vector3 newDropPosition)
        {
            instance.secondsToTake *= (float)((100.0 - config.SpeedUpPlanePercentage) / 100.0);
        }

        private void OnSupplyDropDropped(BaseEntity baseEntity, CargoPlane instance)
        {
            var rb = baseEntity.GetComponent<Rigidbody>();
            if (rb != null)
            {
                rb.drag = config.DropDrag;
            }

            if (airdropOwners.TryGetValue(instance, out ulong teamid))
            {
                airdropOwners.Remove(instance);
                airdropOwners[baseEntity] = teamid;
            }

            if (config.DespawnTime > 0f)
            {
                baseEntity.Invoke(() =>
                {
                    if (baseEntity != null)
                        baseEntity.Kill();
                }, config.DespawnTime);
            }
        }

        void OnCargoPlaneSignaled(CargoPlane cargoPlane, SupplySignal supplySignal)
        {
            if (airdropOwners.TryGetValue(supplySignal, out ulong teamid))
            {
                airdropOwners.Remove(supplySignal);
                airdropOwners[cargoPlane] = teamid;
            }

            if (supplySignal.skinID != 0) return;
            if (config.SmokeDuration >= 210f) return;

            supplySignal.Invoke(() => HandleFinishUp(supplySignal), 0.1f + config.SmokeDuration);
        }

        void HandleFinishUp(SupplySignal signal)
        {
            signal.FinishUp();
        }

        void OnExplosiveThrown(BasePlayer player, SupplySignal entity) => CanThrowAirDrop(player, entity);
        void OnExplosiveDropped(BasePlayer player, SupplySignal entity, ThrownWeapon item) => CanThrowAirDrop(player, entity);

        private void CanThrowAirDrop(BasePlayer player, SupplySignal entity)
        {
            if (player == null || entity == null) return;
            if (airdropOwners.ContainsKey(entity)) return;

            ulong teamid = player.Team != null ? player.Team.teamID : player.userID;
            float now = Time.time;

            if (config.SupplyCooldownTime > 0f && teamCooldownUntil.TryGetValue(teamid, out float readyAt) && now < readyAt)
            {
                player.ChatMessage(Msg(MsgCooldown, player, Mathf.CeilToInt(readyAt - now)));
                RejectThrow(player, entity);
                return;
            }

            if (config.SupplyMaxAlive > 0)
            {
                int alive = PurgeAndCountAlive(teamid);
                if (alive >= config.SupplyMaxAlive)
                {
                    player.ChatMessage(Msg(MsgMaxAlive, player, config.SupplyMaxAlive));
                    RejectThrow(player, entity);
                    return;
                }
            }

            if (config.SupplyCooldownTime > 0f)
                teamCooldownUntil[teamid] = now + config.SupplyCooldownTime;

            if (config.SupplyMaxAlive > 0)
                airdropOwners[entity] = teamid;
        }

        private void RejectThrow(BasePlayer player, SupplySignal entity)
        {
            entity.KillMessage();
            ReturnSupplyDrop(player);
        }

        private int PurgeAndCountAlive(ulong teamid)
        {
            int count = 0;
            List<BaseEntity> dead = null;
            foreach (var kv in airdropOwners)
            {
                if (kv.Key == null || kv.Key.IsDestroyed)
                {
                    if (dead == null) dead = new List<BaseEntity>();
                    dead.Add(kv.Key);
                    continue;
                }
                if (kv.Value == teamid)
                    count++;
            }
            if (dead != null)
            {
                foreach (var e in dead)
                    airdropOwners.Remove(e);
            }
            return count;
        }

        private void ReturnSupplyDrop(BasePlayer player)
        {
            Item supplysignal = ItemManager.CreateByItemID(1397052267, 1);
            player.GiveItem(supplysignal);
        }
    }
}