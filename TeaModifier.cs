using Newtonsoft.Json;
using Oxide.Core;
using Oxide.Core.Plugins;
using System;
using System.Collections.Generic;

namespace Oxide.Plugins
{
    [Info("TeaModifier", "khan", "1.0.1")]
    [Description("Changes the super tea's yield modifiers and duration for players with the bunker permission")]
    public class TeaModifier : RustPlugin
    {
        private const int TeaId = -1003665711;
        private const string Use = "teamodifier.bunker";
        private static Configuration _config;
        private class Configuration
        {
            [JsonProperty("Ore modifier")]
            public float Ore = 4f;
            [JsonProperty("Wood modifier")]
            public float Wood = 5f;
            [JsonProperty("Scrap modifier")]
            public float Scrap = 5f;
            [JsonProperty("Duration [seconds]")]
            public float Duration = 3600f;
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
            permission.RegisterPermission(Use, this);
        }

        private void Unload() => _config = null;

        private object OnPlayerAddModifiers(BasePlayer player, Item item, ItemModConsumable consumable)
        {
            if (item.info.itemid != TeaId || !permission.UserHasPermission(player.UserIDString, Use)) return null;

            // consumable.modifiers is the tea's shared item definition, used by every player on the server.
            // Never edit it - give this player their own copies with the boosted values instead.
            var modifiers = new List<ModifierDefintion>(consumable.modifiers.Count);

            foreach (var mod in consumable.modifiers)
            {
                var copy = new ModifierDefintion
                {
                    type = mod.type,
                    source = mod.source,
                    value = mod.value,
                    duration = mod.duration
                };

                switch (mod.type)
                {
                    case Modifier.ModifierType.Ore_Yield: copy.value = _config.Ore; copy.duration = _config.Duration; break;
                    case Modifier.ModifierType.Wood_Yield: copy.value = _config.Wood; copy.duration = _config.Duration; break;
                    case Modifier.ModifierType.Scrap_Yield: copy.value = _config.Scrap; copy.duration = _config.Duration; break;
                }

                modifiers.Add(copy);
            }

            player.modifiers.Add(modifiers);
            return true; // we've applied the modifiers ourselves, so stop the game adding the defaults as well
        }
    }
}
