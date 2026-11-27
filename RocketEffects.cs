using HarmonyLib;
using Network;
using Newtonsoft.Json;
using Oxide.Core.Plugins;
using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace Oxide.Plugins
{
    [Info("RocketEffects", "Whispers88", "1.0.1")]
    public class RocketEffects : RustPlugin
    {
        public static RocketEffects Instance;
        public static string rocketEffect = "assets/prefabs/weapons/rocketlauncher/effects/rocket_explosion.prefab";
        private static string replaceEffect;
        #region Configuration

        private Configuration config;

        public class Configuration
        {
            [JsonProperty("Replacement effect prefab")]
            public string ReplacementEffect = "assets/prefabs/weapons/beancan grenade/effects/beancan_grenade_explosion.prefab";

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
            replaceEffect = config.ReplacementEffect;
        }

        [HarmonyPatch(typeof(Effect.server), "Run", new Type[] { typeof(string), typeof(Vector3), typeof(Vector3), typeof(Connection), typeof(bool), typeof(List<Connection>), typeof(int), typeof(Effect.Type) }), AutoPatch]
        public static class Effect_Run_Patch
        {
            // Rust removed Effect.reusableInstance. Instead of building and sending our own
            // effect, swap the prefab name and let the vanilla Effect.server.Run send it.
            [HarmonyPrefix]
            static void Prefix(ref string strName)
            {
                if (strName != rocketEffect || string.IsNullOrEmpty(replaceEffect))
                    return;

                strName = replaceEffect;
            }
        }
    }
}


