using Newtonsoft.Json;
using Oxide.Core;
using Oxide.Core.Configuration;
using Oxide.Core.Libraries.Covalence;
using Oxide.Core.Plugins;
using Oxide.Game.Rust.Libraries;
using System;
using System.Collections.Generic;
using UnityEngine;

namespace Oxide.Plugins
{
    [Info("KillFeed", "Whispers88", "1.0.3")]
    [Description("Simple kill feed msgs")]
    public class KillFeed : RustPlugin
    {
        #region Classes

        [JsonObject]
        private class Configuration
        {
            [JsonProperty("Round distance to nearest whole number")]
            public bool roundDistance { get; private set; }

            [JsonProperty("Distance decimal places (used when Round distance is false)")]
            public int distanceDecimalPlaces { get; private set; }

            [JsonProperty("ChatID")]
            public ulong chatId { get; private set; }

            [JsonProperty("Version Number")]
            public VersionNumber versionNumber { get; private set; }

            public static Configuration Generate(VersionNumber versionNumber)
            {
                return new Configuration
                {
                    chatId = 76561198152495837,
                    distanceDecimalPlaces = 1,
                    roundDistance = true,
                    versionNumber = versionNumber
                };
            }

            public void Validate(DynamicConfigFile configFile, VersionNumber versionNumber)
            {
                if (this.versionNumber != versionNumber)
                    this.versionNumber = versionNumber;

                configFile.WriteObject(this);
            }

        }

        #endregion

        #region Constants & Variables

        private static readonly string KILLFEED_CLANHIDE_PERM = "killfeed.clanhide";
        private static readonly string KILLFEED_HIDE_PERM = "killfeed.hide";

        #region Configuration

        private Configuration config;

        #endregion

        #region Plugin References

        [PluginReference]
        private Plugin ClanChat;

        #endregion

        private readonly Player Player = Interface.Oxide.GetLibrary<Player>();

        #endregion

        #region Initialisation

        protected override void LoadDefaultConfig()
        {
            if (!Config.Exists())
            {
                config = Configuration.Generate(Version);
                Config.WriteObject(config);
            }
            else
            {
                config = Config.ReadObject<Configuration>();
                config.Validate(Config, Version);
            }
        }

        protected override void LoadDefaultMessages()
        {
            lang.RegisterMessages(new Dictionary<string, string>()
            {
                ["ClanKillToggle"] = "Clan kill feed messages are now {0}",
                ["Disabled"] = "disabled",
                ["Enabled"] = "enabled",
                ["KillMessage"] = "<color=#F44350>{0}</color> killed {1} from <color=#F44350>{2}</color> meters away with a <color=#F44350>{3}</color>",
                ["KillToggle"] = "Kill feed messages are now {0}"
            }, this);
        }

        private void OnServerInitialized()
        {
            LoadDefaultConfig();
            LoadDefaultMessages();

            AddCovalenceCommand("clanfeed", "ClanFeedCommand");
            AddCovalenceCommand("killfeed", "KillFeedCommand");

            permission.RegisterPermission(KILLFEED_CLANHIDE_PERM, this);
            permission.RegisterPermission(KILLFEED_HIDE_PERM, this);
        }

        #endregion

        #region Commands

        #region Console Commands

        private void ClanFeedCommand(IPlayer player, string command, string[] args)
        {
            BasePlayer basePlayer = player.Object as BasePlayer;

            if (basePlayer == null)
                return;

            if (!player.HasPermission(KILLFEED_CLANHIDE_PERM))
            {
                permission.GrantUserPermission(player.Id, KILLFEED_CLANHIDE_PERM, this);
                SendLMsg(basePlayer, "ClanKillToggle", GetLMsg(basePlayer, "Disabled"));
                return;
            }

            permission.RevokeUserPermission(player.Id, KILLFEED_CLANHIDE_PERM);
            SendLMsg(basePlayer, "ClanKillToggle", GetLMsg(basePlayer, "Enabled"));
        }

        private void KillFeedCommand(IPlayer player, string command, string[] args)
        {
            BasePlayer basePlayer = player.Object as BasePlayer;

            if (basePlayer == null)
                return;

            if (!player.HasPermission(KILLFEED_HIDE_PERM))
            {
                permission.GrantUserPermission(player.Id, KILLFEED_HIDE_PERM, this);
                SendLMsg(basePlayer, "KillToggle", GetLMsg(basePlayer, "Disabled"));
                return;
            }

            permission.RevokeUserPermission(player.Id, KILLFEED_HIDE_PERM);
            SendLMsg(basePlayer, "KillToggle", GetLMsg(basePlayer, "Enabled"));
        }

        #endregion

        #endregion

        #region Oxide Hooks

        private void OnPlayerDeath(BasePlayer player, HitInfo info)
        {
            if (player == null || info == null || player.IsNpc)
                return;

            BasePlayer initiatorPlayer = info.InitiatorPlayer;

            if (initiatorPlayer == null || initiatorPlayer.IsNpc || initiatorPlayer.userID == player.userID)
                return;

            string weapon = info.Weapon?.GetItem()?.info.displayName.english ?? info.WeaponPrefab?.ShortPrefabName ?? "Unknown";
            float distance = Vector3.Distance(player.transform.position, initiatorPlayer.transform.position);

            NotifyPlayer(initiatorPlayer, player, weapon, distance);
        }

        #endregion

        #region Utility Methods

        private string GetLMsg(BasePlayer player, string key, params string[] format) => format != null && format.Length > 0 ? string.Format(lang.GetMessage(key, this, player.UserIDString), format) : lang.GetMessage(key, this, player.UserIDString);

        private string GetName(BasePlayer player)
        {
            string name = ClanChat?.Call<string>("GetName", player.userID.Get());

            return string.IsNullOrEmpty(name) ? player.displayName : name;
        }

        private void NotifyKillerTeam(BasePlayer killer, BasePlayer killed, string[] format)
        {
            if (killer.Team == null || killer.Team.teamID == 0)
                return;

            var online = killer.Team.GetOnlineMemberConnections();

            if (online == null)
                return;

            foreach (var connection in online)
            {
                BasePlayer member = connection.player as BasePlayer;

                if (member == null || killer.userID == member.userID || killed.userID == member.userID || permission.UserHasPermission(member.UserIDString, KILLFEED_CLANHIDE_PERM))
                    continue;

                if (member.IsConnected)
                    SendLMsg(member, "KillMessage", format);
            }
        }

        private void NotifyPlayer(BasePlayer killer, BasePlayer killed, string weapon, float distance)
        {
            double distanceValue = Math.Round(distance, config.roundDistance ? 0 : Mathf.Clamp(config.distanceDecimalPlaces, 0, 15));
            string[] format = { GetName(killer), GetName(killed), $"{distanceValue}", weapon };

            if (killer.IsConnected && !permission.UserHasPermission(killer.UserIDString, KILLFEED_HIDE_PERM))
                SendLMsg(killer, "KillMessage", format);

            if (killed.IsConnected && !permission.UserHasPermission(killed.UserIDString, KILLFEED_HIDE_PERM))
                SendLMsg(killed, "KillMessage", format);

            NotifyKillerTeam(killer, killed, format);
        }

        private void SendLMsg(BasePlayer player, string key, params string[] format) => SendMsg(player, lang.GetMessage(key, this, player.UserIDString), format);

        private void SendMsg(BasePlayer player, string message, params string[] format)
        {
            if (format != null && format.Length > 0)
                message = string.Format(message, format);

            if (player.IsConnected)
                Player.Message(player, message, config.chatId);
            else
                Puts(message);
        }

        #endregion
    }
}
