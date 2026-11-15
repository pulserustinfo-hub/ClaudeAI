using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using UnityEngine;

namespace Oxide.Plugins
{
    [Info("PulseRecycler", "Nathan", "1.3.0")]
    internal class PulseRecycler : RustPlugin
    {
        #region Fields

        private Configuration _config;
        private readonly List<RecyclerTypeConfigSnapshot> _typeConfigSnapshots = new List<RecyclerTypeConfigSnapshot>();

        #endregion

        #region Hooks

        private void OnServerInitialized()
        {
            ApplyRecyclerTypeConfigs();
        }

        private void Unload()
        {
            RestoreRecyclerTypeConfigs();
        }

        #endregion

        #region Recycler Type Config

        private void ApplyRecyclerTypeConfigs()
        {
            RestoreRecyclerTypeConfigs();

            var recyclerConfig = RecyclerConfig.instance;
            if (recyclerConfig == null || recyclerConfig.recyclerTypeConfigs == null)
            {
                PrintWarning("RecyclerConfig.instance is unavailable; recycle settings were not applied");
                return;
            }

            var requiredStageChanged = false;

            foreach (var typeConfig in recyclerConfig.recyclerTypeConfigs)
            {
                if (typeConfig == null)
                    continue;

                if (!TryGetSettings(typeConfig.recyclerType, out var settings))
                {
                    PrintWarning($"No plugin settings for recycler type {typeConfig.recyclerType}; skipping");
                    continue;
                }

                _typeConfigSnapshots.Add(new RecyclerTypeConfigSnapshot(typeConfig));
                typeConfig.duration = Mathf.Max(0f, settings.Duration);
                typeConfig.efficiency = Mathf.Max(0f, settings.Efficiency);
                typeConfig.powergridDuration = Mathf.Max(0f, settings.PowergridDuration);
                typeConfig.powergridEfficiency = Mathf.Max(0f, settings.PowergridEfficiency);

                // A recycler whose type needs a power grid stage cannot be switched on below that stage,
                // so none of the values above matter for it until this allows it to run.
                if (settings.RequiredPowergridStage >= 0 && typeConfig.requiredPowergridStageToUse != settings.RequiredPowergridStage)
                {
                    typeConfig.requiredPowergridStageToUse = settings.RequiredPowergridStage;
                    requiredStageChanged = true;
                }

                Puts(DescribeTypeConfig(typeConfig));
            }

            if (requiredStageChanged)
                RefreshRecyclerPowerState();
        }

        private void RestoreRecyclerTypeConfigs()
        {
            var requiredStageChanged = false;

            foreach (var snapshot in _typeConfigSnapshots)
            {
                if (snapshot.Restore())
                    requiredStageChanged = true;
            }

            _typeConfigSnapshots.Clear();

            if (requiredStageChanged)
                RefreshRecyclerPowerState();
        }

        // Each recycler carries a "receiving power" flag worked out from the stage its type requires. The server
        // and the players' clients both read it, so it is recomputed whenever this plugin changes that stage.
        // One pass over the entity list, and only when the required stage actually changed.
        private void RefreshRecyclerPowerState()
        {
            foreach (var networkable in BaseNetworkable.serverEntities)
            {
                var recycler = networkable as Recycler;
                if (recycler != null && !recycler.IsDestroyed)
                    recycler.Server_RefreshPowergridState();
            }
        }

        private static string DescribeTypeConfig(RecyclerConfig.RecyclerTypeConfig typeConfig)
        {
            var usable = typeConfig.requiredPowergridStageToUse > 0
                ? $"needs power grid stage {typeConfig.requiredPowergridStageToUse} to be switched on"
                : "usable without power";

            return $"{typeConfig.recyclerType}: every {typeConfig.duration:0.##}s at {typeConfig.efficiency:0.##}"
                + $" (with grid power: every {typeConfig.powergridDuration:0.##}s at {typeConfig.powergridEfficiency:0.##}), {usable}";
        }

        private bool TryGetSettings(RecyclerConfig.RecyclerType recyclerType, out RecyclerTypeSettings settings)
        {
            switch (recyclerType)
            {
                case RecyclerConfig.RecyclerType.Green:
                    settings = _config.Green;
                    return settings != null;
                case RecyclerConfig.RecyclerType.Yellow:
                    settings = _config.Yellow;
                    return settings != null;
                case RecyclerConfig.RecyclerType.Red:
                    settings = _config.Red;
                    return settings != null;
                default:
                    settings = null;
                    return false;
            }
        }

        private class RecyclerTypeConfigSnapshot
        {
            private readonly RecyclerConfig.RecyclerTypeConfig _typeConfig;
            private readonly float _efficiency;
            private readonly float _duration;
            private readonly float _powergridEfficiency;
            private readonly float _powergridDuration;
            private readonly int _requiredPowergridStageToUse;

            public RecyclerTypeConfigSnapshot(RecyclerConfig.RecyclerTypeConfig typeConfig)
            {
                _typeConfig = typeConfig;
                _efficiency = typeConfig.efficiency;
                _duration = typeConfig.duration;
                _powergridEfficiency = typeConfig.powergridEfficiency;
                _powergridDuration = typeConfig.powergridDuration;
                _requiredPowergridStageToUse = typeConfig.requiredPowergridStageToUse;
            }

            // Returns true if the stage required to use this type was put back to a different value.
            public bool Restore()
            {
                if (_typeConfig == null)
                    return false;

                _typeConfig.efficiency = _efficiency;
                _typeConfig.duration = _duration;
                _typeConfig.powergridEfficiency = _powergridEfficiency;
                _typeConfig.powergridDuration = _powergridDuration;

                if (_typeConfig.requiredPowergridStageToUse == _requiredPowergridStageToUse)
                    return false;

                _typeConfig.requiredPowergridStageToUse = _requiredPowergridStageToUse;
                return true;
            }
        }

        #endregion

        #region Status

        [ConsoleCommand("pulserecycler.status")]
        private void StatusCommand(ConsoleSystem.Arg arg)
        {
            if (!arg.IsAdmin)
                return;

            var recyclerConfig = RecyclerConfig.instance;
            if (recyclerConfig == null || recyclerConfig.recyclerTypeConfigs == null)
            {
                arg.ReplyWith("RecyclerConfig.instance is unavailable");
                return;
            }

            var text = new StringBuilder();
            text.AppendLine($"{Name} {Version}: values the game is using right now");
            text.AppendLine($"Power grid: enabled {Powergrid.enabled}, stage {PowergridManager.GetCurrentStage(true)} of {PowergridStageConfig.instance.GetNumberOfStages()}, greenRecyclerFullEfficiencyStage {Powergrid.greenRecyclerFullEfficiencyStage}");

            foreach (var typeConfig in recyclerConfig.recyclerTypeConfigs)
            {
                if (typeConfig == null)
                    continue;

                text.AppendLine(DescribeTypeConfig(typeConfig)
                    + $"; grid values apply from stage {typeConfig.efficiencyBuffPowergridStage} (efficiency) / {typeConfig.durationBuffPowergridStage} (duration), 0 = never");
            }

            // By the type each recycler counts as right now (a yellow one outside a safe zone counts as green).
            var total = new int[3];
            var unpowered = new int[3];
            foreach (var networkable in BaseNetworkable.serverEntities)
            {
                var recycler = networkable as Recycler;
                if (recycler == null || recycler.IsDestroyed)
                    continue;

                var type = (int)recycler.GetRecyclerType();
                if (type < 0 || type >= total.Length)
                    continue;

                total[type]++;
                if (recycler.GetRecyclerState() == Recycler.RecyclerState.Unpowered)
                    unpowered[type]++;
            }

            for (var type = 0; type < total.Length; type++)
                text.AppendLine($"{(RecyclerConfig.RecyclerType)type} recyclers on the map: {total[type]}, of which {unpowered[type]} cannot be switched on at the current grid stage");

            arg.ReplyWith(text.ToString());
        }

        #endregion

        #region Configuration

        [JsonObject(MemberSerialization.OptIn)]
        private class RecyclerTypeSettings
        {
            [JsonProperty("Duration (seconds)")]
            public float Duration = 5f;

            [JsonProperty("Efficiency")]
            public float Efficiency = 0.6f;

            [JsonProperty("Powergrid duration (seconds)")]
            public float PowergridDuration = 5f;

            [JsonProperty("Powergrid efficiency")]
            public float PowergridEfficiency = 0.6f;

            [JsonProperty("Power grid stage required to use (-1 = leave as the game has it, 0 = usable without power)")]
            public int RequiredPowergridStage = -1;
        }

        [JsonObject(MemberSerialization.OptIn)]
        private class Configuration : BaseConfiguration
        {
            [JsonProperty("Green")]
            public RecyclerTypeSettings Green = new RecyclerTypeSettings();

            [JsonProperty("Yellow")]
            public RecyclerTypeSettings Yellow = new RecyclerTypeSettings();

            [JsonProperty("Red")]
            public RecyclerTypeSettings Red = new RecyclerTypeSettings();
        }

        private Configuration GetDefaultConfig() => new Configuration();

        [JsonObject(MemberSerialization.OptIn)]
        private class BaseConfiguration
        {
            public string ToJson() => JsonConvert.SerializeObject(this);

            public Dictionary<string, object> ToDictionary() => JsonHelper.Deserialize(ToJson()) as Dictionary<string, object>;
        }

        private static class JsonHelper
        {
            public static object Deserialize(string json) => ToObject(JToken.Parse(json));

            private static object ToObject(JToken token)
            {
                switch (token.Type)
                {
                    case JTokenType.Object:
                        return token.Children<JProperty>()
                            .ToDictionary(prop => prop.Name, prop => ToObject(prop.Value));

                    case JTokenType.Array:
                        return token.Select(ToObject).ToList();

                    default:
                        return ((JValue)token).Value;
                }
            }
        }

        private bool MaybeUpdateConfig(BaseConfiguration config)
        {
            var currentWithDefaults = config.ToDictionary();
            var currentRaw = Config.ToDictionary(x => x.Key, x => x.Value);
            return MaybeUpdateConfigSection(currentWithDefaults, currentRaw);
        }

        private bool MaybeUpdateConfigSection(Dictionary<string, object> currentWithDefaults, Dictionary<string, object> currentRaw)
        {
            var changed = false;

            foreach (var key in currentWithDefaults.Keys)
            {
                if (currentRaw.TryGetValue(key, out var currentRawValue))
                {
                    if (currentWithDefaults[key] is Dictionary<string, object> defaultDictValue
                        && currentRawValue is Dictionary<string, object> currentDictValue)
                    {
                        if (MaybeUpdateConfigSection(defaultDictValue, currentDictValue))
                            changed = true;
                    }
                }
                else
                {
                    currentRaw[key] = currentWithDefaults[key];
                    changed = true;
                }
            }

            return changed;
        }

        protected override void LoadDefaultConfig() => _config = GetDefaultConfig();

        protected override void LoadConfig()
        {
            base.LoadConfig();
            try
            {
                _config = Config.ReadObject<Configuration>();
                if (_config == null)
                    throw new JsonException();

                if (_config.Green == null)
                    _config.Green = new RecyclerTypeSettings();
                if (_config.Yellow == null)
                    _config.Yellow = new RecyclerTypeSettings();
                if (_config.Red == null)
                    _config.Red = new RecyclerTypeSettings();

                if (MaybeUpdateConfig(_config))
                {
                    Puts("Configuration appears to be outdated; updating and saving");
                    SaveConfig();
                }
            }
            catch (Exception e)
            {
                PrintError(e.Message);
                PrintWarning($"Configuration file {Name}.json is invalid; using defaults");
                LoadDefaultConfig();
            }
        }

        protected override void SaveConfig()
        {
            Puts($"Configuration changes saved to {Name}.json");
            Config.WriteObject(_config, true);
        }

        #endregion
    }
}
