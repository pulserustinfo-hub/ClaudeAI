using System;
using System.Collections.Generic;
using HarmonyLib;
using Newtonsoft.Json;
using Oxide.Core.Plugins;

namespace Oxide.Plugins
{
    [Info("PulseStandupOnDown", "Mevent.Team", "1.1.0")]
    [Description("Downed players with permission automatically stand up after a configurable time")]
    public class PulseStandupOnDown : RustPlugin
    {
        private const string Use = "pulsestandupondown.use";

        private static PulseStandupOnDown _instance;
        private static Configuration _config;

        private readonly Dictionary<ulong, Timer> _standupTimers = new();

        private class Configuration
        {
            [JsonProperty("Crawling recovery time [seconds]")]
            public float CrawlingRecoveryTime = 10f;

            [JsonProperty("Incapacitated recovery time [seconds]")]
            public float IncapacitatedRecoveryTime = 15f;

            [JsonProperty("Heal after standup (0 to disable)")]
            public float HealAmount = 5f;
        }

        protected override void LoadDefaultConfig()
        {
            _config = new Configuration();
            SaveConfig();
        }

        protected override void LoadConfig()
        {
            base.LoadConfig();

            try
            {
                _config = Config.ReadObject<Configuration>();
                if (_config == null) LoadDefaultConfig();
                else SaveConfig(); // writes any new/renamed keys back to the file
            }
            catch (Exception ex)
            {
                PrintWarning("Failed to load config file (is the config file corrupt?) (" + ex.Message + ")");
                PrintError("Please verify your config file at https://jsonlint.com/ - using defaults for now");
                _config = new Configuration();
            }
        }

        protected override void SaveConfig() => Config.WriteObject(_config, true);

        private void Init()
        {
            _instance = this;
            permission.RegisterPermission(Use, this);
        }

        private void Unload()
        {
            // Oxide destroys this plugin's timers on unload, so no pending standups survive a reload.
            _instance = null;
            _config = null;
        }

        private bool HasPermission(BasePlayer player) =>
            player.userID.IsSteamId() && permission.UserHasPermission(player.UserIDString, Use);

        private void OnPlayerWound(BasePlayer player, HitInfo info)
        {
            if (player == null || !player.IsConnected || !HasPermission(player)) return;

            player.CancelInvoke(player.WoundingTick);

            var recoveryTime = player.IsIncapacitated()
                ? _config.IncapacitatedRecoveryTime
                : _config.CrawlingRecoveryTime;

            player.woundedDuration = recoveryTime;
            player.ApplyWoundedStartTime();
            player.SendWoundedInformation(recoveryTime);

            var userId = player.userID.Get();

            // Replace any timer left over from an earlier down, so it can't stand the player up early.
            if (_standupTimers.TryGetValue(userId, out var existing)) existing?.Destroy();

            _standupTimers[userId] = timer.Once(recoveryTime, () =>
            {
                _standupTimers.Remove(userId);

                if (player == null || player.IsDead() || !player.IsWounded() || !player.IsConnected) return;

                player.StopWounded();
                if (_config.HealAmount > 0f) player.Heal(_config.HealAmount);
            });
        }

        [AutoPatch]
        [HarmonyPatch(typeof(BasePlayer), nameof(BasePlayer.GetRecoveryChance))]
        private static class GetRecoveryChancePatch
        {
            private static bool Prefix(BasePlayer __instance, ref float __result)
            {
                if (_instance == null || !_instance.HasPermission(__instance)) return true;

                __result = 1f;
                return false;
            }
        }
    }
}
