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
    [Info("KillFeed", "Whispers88", "1.0.1")]
    [Description("Simple kill feed msgs")]

    public class KillFeed : CovalencePlugin
    {
        #region Localization

        protected override void LoadDefaultMessages()
        {
            lang.RegisterMessages(new Dictionary<string, string>
            {
                ["killtoggle"] = "Kill feed messages are now {0}",
                ["ckilltoggle"] = "Clan kill feed messages are now {0}",
            }, this);
        }

        #endregion Localization

        #region Configuration

        private Configuration config;

        public class Configuration
        {
            [JsonProperty("Message format")]
            public string KillMessageFormat = "<color=#F44350>{0}</color> killed {1} from <color=#F44350>{2}</color> meters away with a <color=#F44350>{3}</color>";

            [JsonProperty("Message title")]
            public string MessageTitle = "KillFeed";

            [JsonProperty("Message color (hex)")]
            public string MessageColor = "#F44350";

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
        private string GetName(ulong player) => ClanChat?.Call<string>("GetName", player) ?? string.Empty;

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
            double distanceValue = config != null && config.RoundDistance
                ? Math.Round(distance, 0)
                : Math.Round(distance, config != null ? config.DistanceDecimalPlaces : 1);

            string format = (config != null && !string.IsNullOrEmpty(config.KillMessageFormat))
                ? config.KillMessageFormat
                : "<color=#F44350>{0}</color> killed {1} from <color=#F44350>{2}</color> meters away with a <color=#F44350>{3}</color>";

            string killMsgFormatted = string.Format(format, GetName(killer.userID.Get()), GetName(killed.userID.Get()), distanceValue, weapon);

            if (!HasPerm(killer.UserIDString, permhide)) Player.Message(killer, killMsgFormatted, config?.ChatID ?? 0);
            if (!HasPerm(killed.UserIDString, permhide)) Player.Message(killed, killMsgFormatted, config?.ChatID ?? 0);
            NotifyKillerTeam(killer, killed, killMsgFormatted);
        }

        void NotifyKillerTeam(BasePlayer killer, BasePlayer killed, string killMsgFormatted)
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

                Player.Message(player, killMsgFormatted, config.ChatID);
            }
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
                ChatMessage(player, "killtoggle", "disabled");
                return;
            }

            permission.RevokeUserPermission(player.UserIDString, permhide);
            ChatMessage(player, "killtoggle", "enabled");
        }

        private void ToggleClanDeathMsgs(IPlayer iplayer, string command, string[] args)
        {
            var player = iplayer.Object as BasePlayer;
            if (player == null) return;

            if (!HasPerm(player.UserIDString, clanHide))
            {
                permission.GrantUserPermission(player.UserIDString, clanHide, this);
                ChatMessage(player, "ckilltoggle", "disabled");
                return;
            }

            permission.RevokeUserPermission(player.UserIDString, clanHide);
            ChatMessage(player, "ckilltoggle", "enabled");
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
