using Newtonsoft.Json;

namespace Oxide.Plugins
{
    [Info("No Heli Fire", "Tryhard", "1.5.0")]
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

        // OnEntitySpawned is the only spawn hook Oxide has, so the per-spawn work stays as in 1.2.6. What changes:
        // while the server restores the save it spawns every saved entity, and 1.2.6 was called for each one.
        // Here the hook is off until OnServerInitialized; the helicopters restored from the save are then changed
        // in one pass and the hook is switched on. The game calls OnServerInitialized in the same call that opens
        // the server to connections (ServerMgr.OpenConnection), so no player can reach a helicopter first.
        // After a reload the same pass also covers helicopters that already exist, which 1.2.6 did not.

        private void Init()
        {
            Unsubscribe(nameof(OnEntitySpawned));
        }

        private void OnServerInitialized()
        {
            if (!configData.mExplo && !configData.mFire && !configData.mGibs
                && !configData.sExplo && !configData.sFire && !configData.sGibs
                && !configData.aExplo && !configData.aFire && !configData.aGibs)
            {
                return;
            }

            foreach (BaseNetworkable entity in BaseNetworkable.serverEntities)
            {
                if (entity is ScrapTransportHelicopter scrap)
                    OnEntitySpawned(scrap);
                else if (entity is Minicopter mini)
                    OnEntitySpawned(mini);
                else if (entity is AttackHelicopter attack)
                    OnEntitySpawned(attack);
            }

            Subscribe(nameof(OnEntitySpawned));
        }


        private void OnEntitySpawned(ScrapTransportHelicopter entity)
        {

            if (configData.sExplo) entity.explosionEffect.guid = null;

            if (configData.sFire) entity.fireBall.guid = null;

            if (configData.sGibs) entity.serverGibs.guid = null;
        }

        private void OnEntitySpawned(Minicopter entity)
        {
            if (configData.mExplo) entity.explosionEffect.guid = null;

            if (configData.mFire) entity.fireBall.guid = null;

            if (configData.mGibs) entity.serverGibs.guid = null;
        }

        private void OnEntitySpawned(AttackHelicopter entity)
        {
            if (configData.aExplo) entity.explosionEffect.guid = null;

            if (configData.aFire) entity.fireBall.guid = null;

            if (configData.aGibs) entity.serverGibs.guid = null;
        }
    }
}