using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace Oxide.Plugins
{
    [Info("PulseRecycler", "Nathan", "1.2.0")]
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
            }
        }

        private void RestoreRecyclerTypeConfigs()
        {
            foreach (var snapshot in _typeConfigSnapshots)
                snapshot.Restore();

            _typeConfigSnapshots.Clear();
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

            public RecyclerTypeConfigSnapshot(RecyclerConfig.RecyclerTypeConfig typeConfig)
            {
                _typeConfig = typeConfig;
                _efficiency = typeConfig.efficiency;
                _duration = typeConfig.duration;
                _powergridEfficiency = typeConfig.powergridEfficiency;
                _powergridDuration = typeConfig.powergridDuration;
            }

            public void Restore()
            {
                if (_typeConfig == null)
                    return;

                _typeConfig.efficiency = _efficiency;
                _typeConfig.duration = _duration;
                _typeConfig.powergridEfficiency = _powergridEfficiency;
                _typeConfig.powergridDuration = _powergridDuration;
            }
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
