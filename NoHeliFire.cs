using Newtonsoft.Json;

namespace Oxide.Plugins
{
    [Info("No Heli Fire", "Tryhard", "1.4.0")]
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


        // The three effects are only used in BaseHelicopter.OnDied, which runs from BaseCombatEntity.Die right
        // after Die has called OnEntityDeath. Clearing them here, on the one helicopter that is dying, gives the
        // same result as clearing them when it spawned. Each entity spawns once and dies at most once (Die
        // returns early if it is already dead), and many never die at all (dropped items, projectiles and
        // anything removed with Kill), so this hook runs far less often than OnEntitySpawned did. It is also
        // not called for every entity restored from the save at boot.

        private void Init()
        {
            if (!configData.mExplo && !configData.mFire && !configData.mGibs
                && !configData.sExplo && !configData.sFire && !configData.sGibs
                && !configData.aExplo && !configData.aFire && !configData.aGibs)
            {
                Unsubscribe(nameof(OnEntityDeath));
            }
        }

        private void OnEntityDeath(ScrapTransportHelicopter entity, HitInfo info)
        {
            if (configData.sExplo) entity.explosionEffect.guid = null;

            if (configData.sFire) entity.fireBall.guid = null;

            if (configData.sGibs) entity.serverGibs.guid = null;
        }

        private void OnEntityDeath(Minicopter entity, HitInfo info)
        {
            if (configData.mExplo) entity.explosionEffect.guid = null;

            if (configData.mFire) entity.fireBall.guid = null;

            if (configData.mGibs) entity.serverGibs.guid = null;
        }

        private void OnEntityDeath(AttackHelicopter entity, HitInfo info)
        {
            if (configData.aExplo) entity.explosionEffect.guid = null;

            if (configData.aFire) entity.fireBall.guid = null;

            if (configData.aGibs) entity.serverGibs.guid = null;
        }
    }
}