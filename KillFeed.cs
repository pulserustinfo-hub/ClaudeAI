using Oxide.Core;
using Oxide.Core.Libraries.Covalence;
using Steamworks;
using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Network;
using Facepunch;
using Newtonsoft.Json;
using Newtonsoft.Json.Serialization;
using System.Linq;
using Oxide.Core.Plugins;
using Oxide.Game.Rust.Libraries;

namespace Oxide.Plugins
{
    [Info("KillFeed", "Whispers88", "1.0.2")]
    [Description("Simple kill feed msgs")]

    public class KillFeed : CovalencePlugin
    {
        #region Localization

        protected override void LoadDefaultMessages()
        {
            lang.RegisterMessages(new Dictionary<string, string>
            {
                ["killmessage"] = "<color=#F44350>{0}</color> killed {1} from <color=#F44350>{2}</color> meters away with a <color=#F44350>{3}</color>",
                ["killtoggle"] = "Kill feed messages are now {0}",
                ["ckilltoggle"] = "Clan kill feed messages are now {0}",
                ["enabled"] = "enabled",
                ["disabled"] = "disabled",
            }, this);
        }

        #endregion Localization

        #region Configuration

        private Configuration config;

        public class Configuration
        {
            [JsonProperty("Round distance to nearest whole number")]
            public bool RoundDistance = true;

            [JsonProperty("Distance decimal places (used when Round distance is false)")]
            public int DistanceDecimalPlaces = 1;

            public ulong ChatID = 76561198152495837;

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
                    throw new JsonException();

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

        private static readonly string permhide = "killfeed.hide";
        private static readonly string clanHide = "killfeed.clanhide";

        [PluginReference] private Plugin ClanChat;

        private string GetName(BasePlayer player)
        {
            string name = ClanChat?.Call<string>("GetName", player.userID.Get());
            return string.IsNullOrEmpty(name) ? player.displayName : name;
        }

        #region Hooks

        Player Player = Interface.Oxide.GetLibrary<Player>();

        void OnServerInitialized()
        {
            permission.RegisterPermission(permhide, this);
            permission.RegisterPermission(clanHide, this);
            AddCovalenceCommand("killfeed", "ToggleDeathMsgs");
            AddCovalenceCommand("clanfeed", "ToggleClanDeathMsgs");
        }

        void OnPlayerDeath(BasePlayer player, HitInfo info)
        {
            if (player == null || info == null || player.IsNpc) return;

            var initiatorPlayer = info.InitiatorPlayer;
            if (initiatorPlayer == null || initiatorPlayer.IsNpc || initiatorPlayer.userID == player.userID)
                return;


            string weapon = info.Weapon?.GetItem()?.info.displayName.english ?? info.WeaponPrefab?.ShortPrefabName ?? "Unknown";
            float distance = Vector3.Distance(player.transform.position, initiatorPlayer.transform.position);
            NotifyPlayer(initiatorPlayer, player, weapon, distance);
        }

        private void NotifyPlayer(BasePlayer killer, BasePlayer killed, string weapon, float distance)
        {
            double distanceValue = Math.Round(distance, config.RoundDistance ? 0 : Mathf.Clamp(config.DistanceDecimalPlaces, 0, 15));
            object[] args = { GetName(killer), GetName(killed), distanceValue, weapon };

            if (!HasPerm(killer.UserIDString, permhide)) SendKillMessage(killer, args);
            if (!HasPerm(killed.UserIDString, permhide)) SendKillMessage(killed, args);
            NotifyKillerTeam(killer, killed, args);
        }

        void NotifyKillerTeam(BasePlayer killer, BasePlayer killed, object[] args)
        {
            if (killer.Team == null || killer.Team.teamID == 0 )
                return;

            var online = killer.Team.GetOnlineMemberConnections();
            if (online == null)
                return;

            foreach (var connection in online)
            {
                var player = connection.player as BasePlayer;
                if (player == null || killer.userID == player.userID || killed.userID == player.userID || HasPerm(player.UserIDString, clanHide))
                    continue;

                SendKillMessage(player, args);
            }
        }

        private void SendKillMessage(BasePlayer player, object[] args)
        {
            if (player.IsConnected)
                Player.Message(player, GetLang("killmessage", player.UserIDString, args), config.ChatID);
        }

        #endregion

        #region Commands
        private void ToggleDeathMsgs(IPlayer iplayer, string command, string[] args)
        {
            var player = iplayer.Object as BasePlayer;
            if (player == null) return;

            if (!HasPerm(player.UserIDString, permhide))
            {
                permission.GrantUserPermission(player.UserIDString, permhide, this);
                ChatMessage(player, "killtoggle", GetLang("disabled", player.UserIDString));
                return;
            }

            permission.RevokeUserPermission(player.UserIDString, permhide);
            ChatMessage(player, "killtoggle", GetLang("enabled", player.UserIDString));
        }

        private void ToggleClanDeathMsgs(IPlayer iplayer, string command, string[] args)
        {
            var player = iplayer.Object as BasePlayer;
            if (player == null) return;

            if (!HasPerm(player.UserIDString, clanHide))
            {
                permission.GrantUserPermission(player.UserIDString, clanHide, this);
                ChatMessage(player, "ckilltoggle", GetLang("disabled", player.UserIDString));
                return;
            }

            permission.RevokeUserPermission(player.UserIDString, clanHide);
            ChatMessage(player, "ckilltoggle", GetLang("enabled", player.UserIDString));
        }
        #endregion

        #region Helpers
        private bool HasPerm(string id, string perm) => permission.UserHasPermission(id, perm);

        private string GetLang(string langKey, string playerId = null, params object[] args)
        {
            return string.Format(lang.GetMessage(langKey, this, playerId), args);
        }
        private void ChatMessage(BasePlayer player, string langKey, params object[] args)
        {
            if (player.IsConnected)
                Player.Message(player, GetLang(langKey, player.UserIDString, args), config.ChatID);
            else Puts(GetLang(langKey, player.UserIDString, args));
        }
        #endregion Helpers
    }
}
