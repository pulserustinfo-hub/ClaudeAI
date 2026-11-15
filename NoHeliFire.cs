﻿using System;
using System.Collections.Generic;
using Newtonsoft.Json;
using Oxide.Core;
using UnityEngine;

namespace Oxide.Plugins
{
    [Info("No Heli Fire", "Tryhard", "1.3.0")]
    [Description("Optionally removes the explosion sound, gibs and fire effect from mini- and scrap helicopters")]
    public class NoHeliFire : RustPlugin
    {
        private ConfigData configData = new ConfigData();

        private class ConfigData
        {
            [JsonProperty(PropertyName = "Disable minicopter gibs")]
            public bool mGibs = true;

            [JsonProperty(PropertyName = "Disable minicopter fire")]
            public bool mFire = true;

            [JsonProperty(PropertyName = "Disable minicopter explosion sound")]
            public bool mExplo = true;



            [JsonProperty(PropertyName = "Disable scraphelicopter gibs")]
            public bool sGibs = true;

            [JsonProperty(PropertyName = "Disable scraphelicopter explosion sound")]
            public bool sExplo = true;

            [JsonProperty(PropertyName = "Disable scraphelicopter fire ")]
            public bool sFire = true;



            [JsonProperty(PropertyName = "Disable attackhelicopter gibs")]
            public bool aGibs = true;

            [JsonProperty(PropertyName = "Disable attackhelicopter explosion sound")]
            public bool aExplo = true;

            [JsonProperty(PropertyName = "Disable attackhelicopter fire ")]
            public bool aFire = true;
        }

        protected override void LoadConfig()
        {
            base.LoadConfig();

            try
            {
                configData = Config.ReadObject<ConfigData>();

                if (configData == null) LoadDefaultConfig();
            }

            catch
            {
                PrintError("Configuration file is corrupt, check your config file at https://jsonlint.com/!");
                LoadDefaultConfig();
                return;
            }

            SaveConfig();
        }

        protected override void LoadDefaultConfig() => configData = new ConfigData();

        protected override void SaveConfig() => Config.WriteObject(configData);

        #region Prefab changes

        // How this works, and why it costs nothing while the server runs:
        // A helicopter only reads these three effects in BaseHelicopter.OnDied, from its own copy of the
        // settings, and every helicopter gets that copy when the server clones it from the prefab template
        // (GameManager.CreateEntity -> Object.Instantiate). Changing the template once therefore covers every
        // helicopter created afterwards, so the plugin no longer listens to OnEntitySpawned, which the game
        // calls for every entity spawned on the server. Helicopters that already exist when the plugin loads
        // (restored from the save, or spawned before a reload) are changed once, in the same pass.

        // The vanilla prefabs for the three helicopter types.
        private static readonly string[] KnownPrefabs =
        {
            "assets/content/vehicles/minicopter/minicopter.entity.prefab",
            "assets/content/vehicles/scrap heli carrier/scraptransporthelicopter.prefab",
            "assets/content/vehicles/attackhelicopter/attackhelicopter.entity.prefab"
        };

        // Any other entity prefab whose path contains one of these is checked as well.
        private static readonly string[] PrefabNameParts = { "minicopter", "scraptransporthelicopter", "attackhelicopter" };

        private class EffectSettings
        {
            public bool Explosion;
            public bool Fire;
            public bool Gibs;

            public bool Any => Explosion || Fire || Gibs;
        }

        // The game's own values on a template, kept so they can be put back on unload.
        private class TemplateRecord
        {
            public BaseHelicopter Template;
            public EffectSettings Disabled;
            public string ExplosionGuid;
            public string FireGuid;
            public string GibsGuid;
        }

        private readonly Dictionary<string, TemplateRecord> _templates = new Dictionary<string, TemplateRecord>(StringComparer.OrdinalIgnoreCase);

        private void OnServerInitialized()
        {
            if (!configData.mExplo && !configData.mFire && !configData.mGibs
                && !configData.sExplo && !configData.sFire && !configData.sGibs
                && !configData.aExplo && !configData.aFire && !configData.aGibs)
            {
                Puts("All options are off; nothing changed");
                return;
            }

            foreach (string path in KnownPrefabs)
                TryChangeTemplate(path);

            string[] entityPrefabs = GameManifest.Current?.entities;
            if (entityPrefabs != null)
            {
                foreach (string path in entityPrefabs)
                {
                    if (!string.IsNullOrEmpty(path) && !_templates.ContainsKey(path) && ContainsAny(path, PrefabNameParts))
                        TryChangeTemplate(path);
                }
            }

            // Helicopters that exist already. Their own prefab is recorded too, in case it is not one of the above.
            int changed = 0;
            foreach (BaseNetworkable networkable in BaseNetworkable.serverEntities)
            {
                BaseHelicopter helicopter = networkable as BaseHelicopter;
                if (helicopter == null || helicopter.IsDestroyed)
                    continue;

                EffectSettings settings = GetSettings(helicopter);
                if (settings == null || !settings.Any)
                    continue;

                if (!string.IsNullOrEmpty(helicopter.PrefabName) && !_templates.ContainsKey(helicopter.PrefabName))
                    TryChangeTemplate(helicopter.PrefabName);

                ClearEffects(helicopter, settings);
                changed++;
            }

            changed += ForEachPooledHelicopter(helicopter =>
            {
                EffectSettings settings = GetSettings(helicopter);
                if (settings != null && settings.Any)
                    ClearEffects(helicopter, settings);
            });

            Puts($"Effects disabled on {_templates.Count} helicopter prefab(s) and {changed} existing helicopter(s)");
        }

        private void Unload()
        {
            foreach (TemplateRecord record in _templates.Values)
            {
                if (record.Template != null)
                    RestoreEffects(record.Template, record);
            }

            // Not worth a pass over every entity when the server is shutting down.
            if (_templates.Count > 0 && !Interface.Oxide.IsShuttingDown)
            {
                foreach (BaseNetworkable networkable in BaseNetworkable.serverEntities)
                {
                    BaseHelicopter helicopter = networkable as BaseHelicopter;
                    if (helicopter != null && !helicopter.IsDestroyed)
                        RestoreFromTemplate(helicopter);
                }

                ForEachPooledHelicopter(RestoreFromTemplate);
            }

            _templates.Clear();
        }

        private void TryChangeTemplate(string path)
        {
            if (_templates.ContainsKey(path))
                return;

            GameObject prefab = GameManager.server.FindPrefab(path);
            if (prefab == null)
                return;

            BaseHelicopter template = prefab.GetComponent<BaseHelicopter>();
            if (template == null)
                return;

            EffectSettings settings = GetSettings(template);
            if (settings == null || !settings.Any)
                return;

            _templates[path] = new TemplateRecord
            {
                Template = template,
                Disabled = settings,
                ExplosionGuid = template.explosionEffect?.guid,
                FireGuid = template.fireBall?.guid,
                GibsGuid = template.serverGibs?.guid
            };

            ClearEffects(template, settings);
        }

        // The same type tests the old OnEntitySpawned handlers made. None of these classes derives from another.
        private EffectSettings GetSettings(BaseHelicopter helicopter)
        {
            if (helicopter is ScrapTransportHelicopter)
                return new EffectSettings { Explosion = configData.sExplo, Fire = configData.sFire, Gibs = configData.sGibs };

            if (helicopter is Minicopter)
                return new EffectSettings { Explosion = configData.mExplo, Fire = configData.mFire, Gibs = configData.mGibs };

            if (helicopter is AttackHelicopter)
                return new EffectSettings { Explosion = configData.aExplo, Fire = configData.aFire, Gibs = configData.aGibs };

            return null;
        }

        // Exactly what the old version did on spawn.
        private static void ClearEffects(BaseHelicopter helicopter, EffectSettings settings)
        {
            if (settings.Explosion && helicopter.explosionEffect != null) helicopter.explosionEffect.guid = null;

            if (settings.Fire && helicopter.fireBall != null) helicopter.fireBall.guid = null;

            if (settings.Gibs && helicopter.serverGibs != null) helicopter.serverGibs.guid = null;
        }

        private static void RestoreEffects(BaseHelicopter helicopter, TemplateRecord record)
        {
            if (record.Disabled.Explosion && helicopter.explosionEffect != null && string.IsNullOrEmpty(helicopter.explosionEffect.guid))
                helicopter.explosionEffect.guid = record.ExplosionGuid;

            if (record.Disabled.Fire && helicopter.fireBall != null && string.IsNullOrEmpty(helicopter.fireBall.guid))
                helicopter.fireBall.guid = record.FireGuid;

            if (record.Disabled.Gibs && helicopter.serverGibs != null && string.IsNullOrEmpty(helicopter.serverGibs.guid))
                helicopter.serverGibs.guid = record.GibsGuid;
        }

        private void RestoreFromTemplate(BaseHelicopter helicopter)
        {
            if (!string.IsNullOrEmpty(helicopter.PrefabName) && _templates.TryGetValue(helicopter.PrefabName, out TemplateRecord record))
                RestoreEffects(helicopter, record);
        }

        // The server strips the pool marker (Poolable is a client-only component), so in practice nothing is
        // pooled here. Covered anyway: a pooled helicopter would otherwise skip the template.
        private static int ForEachPooledHelicopter(Action<BaseHelicopter> action)
        {
            int count = 0;
            Dictionary<uint, PrefabPool> storage = GameManager.server?.pool?.storage;
            if (storage == null)
                return count;

            foreach (PrefabPool pool in storage.Values)
            {
                if (pool?.stack == null)
                    continue;

                foreach (Poolable poolable in pool.stack)
                {
                    if (poolable == null)
                        continue;

                    BaseHelicopter helicopter = poolable.GetComponent<BaseHelicopter>();
                    if (helicopter == null)
                        continue;

                    action(helicopter);
                    count++;
                }
            }

            return count;
        }

        private static bool ContainsAny(string text, string[] parts)
        {
            foreach (string part in parts)
            {
                if (text.IndexOf(part, StringComparison.OrdinalIgnoreCase) >= 0)
                    return true;
            }

            return false;
        }

        #endregion
    }
}
