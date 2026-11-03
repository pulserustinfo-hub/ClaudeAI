using HarmonyLib;
using System;
using System.IO;
using System.Reflection;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using Newtonsoft.Json;
using Oxide.Core;
using Oxide.Core.Plugins;
using UnityEngine;
using UnityEngine.AI;
using Random = UnityEngine.Random;

namespace Oxide.Plugins
{
    [Info("Spawn Groups Override", "Khan", "1.2.0")]
    [Description("Overrides Vanilla Spawn Times")]
    public class SpawnGroupsOverride : RustPlugin
    {

        #region Fields

        private readonly Dictionary<string, OverRide> _spawnGroups = new Dictionary<string, OverRide>
        {
            ["HackedCrateSpawn"] = new OverRide(),
            ["spawner_elite_crate"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crate Spawner_Elite"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["elite_crate_spawner"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Elite Crate Spawner Powergrid Loot Room"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Elite Spawner_L6"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Elite Spawner_L4"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Elite Spawner_Lab"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Elite Spawner"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Military Crate Spawner Powergrid Loot Room"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["CrateSpawner"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crate Spawner"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crate Spawner_L6"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crate Spawner_L5"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crate Spawner_L4"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crate Spawner_L3"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crate Spawner Quarters"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["spawner_normal_crates"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["spawner_crate_normal_old_style"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["spawner_food_crates"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["spawner_medical_crate"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["spawner_oil_barrel"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["spawner_fuel"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["spawner_tools_crate"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["spawner_ammo_crate"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["spawner_vehicle_parts_crate"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["spawner_tech_parts_crate"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["VehiclePartSpawner"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Minecrate_spawner"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Minecrate Spawner"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crate Spawner Office (1)"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crate Spawner Office"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Mine_crate_spawner"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Basic Crate Spawner"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crate Spawner Container Office"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crate Spawner Low cabin"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crate Spawner High cabin"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crates_spawner"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["JungleCrate_Spawner"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crate Spawner Tower"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crate Spawner Armory"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crate Spawner Average"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crate Spawner Interior - Second"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crate Spawner Interior - First"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crate Spawner Above"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crate Spawner Control Room"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crate Spawner Plant"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crate Spawner Warehouse"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crate Spawner_Blend"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crate Spawner_Excellent"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crate Spawner_Average"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crate Spawner Tier2 (1)"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crate Spawner Tier2"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Low Crate Spawner"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crates_spawner_tier2"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crate Spawner Bandit Core"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Crate Spawner_Lab"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Barrel/Crate Spawner"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 90 },
            ["Barrel Spawner (2)"] = new OverRide(),
            ["Barrel Spawner (1)"] = new OverRide(),
            ["Barrel_spawner"] = new OverRide(),
            ["Barrel Spawner Plant"] = new OverRide(),
            ["Barrel Spawner Tower"] = new OverRide(),
            ["Spawner Barrels"] = new OverRide(),
            ["Barrels_spawner"] = new OverRide(),
            ["Barrel Spawner"] = new OverRide(),
            ["BarrelSpawner"] = new OverRide(),
            ["Oil Barrel Spawner"] = new OverRide(),
            ["Oil_Barrels_spawner"] = new OverRide(),
            ["diesel_barrel_spawner"] = new OverRide(),
            ["Oil_spawner"] = new OverRide(),
            ["Diesel Spawner"] = new OverRide{ OverrideRespawnTime = true, SpawnTime = 180 },
            ["Fuel"] = new OverRide(),
            ["Spawner Food"] = new OverRide(),
            ["Food Spawner"] = new OverRide(),
            ["Loot Spawner"] = new OverRide(),
            ["Minecart Spawner"] = new OverRide(),
            ["Minecart_spawner"] = new OverRide(),
            ["Ore LootSpawner"] = new OverRide(),
            ["Sulfur spawner"] = new OverRide(),
            ["Logs spawner"] = new OverRide(),
            ["CacheSpawner"] = new OverRide(),
            ["card_spawner_blue"] = new OverRide(),
            ["card_spawner_red"] = new OverRide(),
            ["card_spawner_green"] = new OverRide(),
            ["ShredableSpawner"] = new OverRide(),
            ["spawner_bp"] = new OverRide(),
            ["spawner_bp_fragment"] = new OverRide(),
            ["spawner_bp_spawner"] = new OverRide(),
            ["Basic BP Spawner (1)"] = new OverRide(),
            ["Basic BP Spawner"] = new OverRide(),
            ["Basic BP Fragment"] = new OverRide(),
            ["basic BP fragment spawner"] = new OverRide(),
            ["Basic BP Fragment Spawner"] = new OverRide(),
            ["Advance Fragment Spawner"] = new OverRide(),
            ["fragment_spawner"] = new OverRide(),
            ["Fragment Spawner"] = new OverRide(),
            ["basic_fragment_spawner"] = new OverRide(),
            ["spawner_advance_fragment"] = new OverRide(),

            ["DwellingSpawner"] = new OverRide(),
            ["DwellingSpawner_300_Corner_DEEP"] = new OverRide(),
            ["DwellingSpawner_300_Corner"] = new OverRide(),
            ["DwellingSpawner_300_Edge"] = new OverRide(),
            ["DwellingSpawner_300_Corridor"] = new OverRide(),
            ["DwellingSpawner_600_Corner"] = new OverRide(),
            ["DwellingSpawner_300_Edge_DEEP"] = new OverRide(),
            ["DwellingSpawner_600_Corridor_Double"] = new OverRide(),

            ["WorkCartSpawner"] = new OverRide(),
            ["SharkSpawner"] = new OverRide(),
            ["door_barricade_b_Spawner"] = new OverRide(),
            ["door_barricade_a_Spawner"] = new OverRide(),
            ["Blue Spawner"] = new OverRide(),
            ["Vehicle Comp Spawner"] = new OverRide(),
            ["Better Vehicle Comp Spawner"] = new OverRide(),
            ["door_barricade_b_Spawner (1)"] = new OverRide(),
            ["door_barricade_a_Spawner (1)"] = new OverRide(),
            ["BarricadeSpawner"] = new OverRide(),
            ["LootStripSpawner"] = new OverRide(),
            ["CraneSpawner"] = new OverRide(),
            ["VanillaRespawnSpawner"] = new OverRide(),
            ["SoftcoreRespawnSpawner"] = new OverRide(),
            ["PlayerRespawnSpawner"] = new OverRide(),
            ["SpawnGroupSnowmobile"] = new OverRide(),
        };

        private readonly Dictionary<string, OverRide> _npcSpawnGroups = new Dictionary<string, OverRide>
        {
            ["ScientistSpawner"] = new OverRide(),
            ["NPCSpawner"] = new OverRide(),
            ["HTNSpawn (4)"] = new OverRide(),
            ["HTNSpawn (3)"] = new OverRide(),
            ["NPCTurretSpawn (4)"] = new OverRide(),
            ["NPCTurretSpawn (3)"] = new OverRide(),
            ["NPCTurretSpawn (2)"] = new OverRide(),
            ["NPCTurretSpawn (1)"] = new OverRide(),
            ["NPCTurretSpawn"] = new OverRide(),
            ["HTNSpawn (10)"] = new OverRide(),
            ["HTNSpawn (9)"] = new OverRide(),
            ["HTNSpawn (8)"] = new OverRide(),
            ["HTNSpawn (7)"] = new OverRide(),
            ["HTNSpawn (6)"] = new OverRide(),
            ["HTNSpawn (5)"] = new OverRide(),
            ["L6"] = new OverRide(),
            ["L5"] = new OverRide(),
            ["L4"] = new OverRide(),
            ["L3"] = new OverRide(),
            ["L2"] = new OverRide(),
            ["L1"] = new OverRide(),
            ["DockSpawner"] = new OverRide(),
            ["ShopkeeperSpawner"] = new OverRide(),
            ["Spawner"] = new OverRide(),
            ["Main HTNSpawn"] = new OverRide(),
            ["Green Card HTNSpawn (10)"] = new OverRide(),
            ["Lab HTNSpawn (9)"] = new OverRide(),
            ["Lab HTNSpawn (8)"] = new OverRide(),
            ["Lab HTNSpawn (7)"] = new OverRide(),
            ["Lab HTNSpawn (6)"] = new OverRide(),
            ["Lab HTNSpawn (5)"] = new OverRide(),
            ["Lab HTNSpawn (4)"] = new OverRide(),
            ["Lab HTNSpawn (3)"] = new OverRide(),
            ["PuzzleTower"] = new OverRide(),
            ["PuzzleRoom1_2"] = new OverRide(),
            ["PuzzleRoom1_1"] = new OverRide(),
            ["PuzzleRoom2"] = new OverRide(),
            ["PuzzleRoomCorridors"] = new OverRide(),
            ["PuzzleRoomOuter"] = new OverRide(),
            ["PuzzleRoomInner"] = new OverRide(),
            ["LowerLevels"] = new OverRide(),
            ["CoreInner"] = new OverRide(),
            ["CoreOuter"] = new OverRide(),
            ["Umbilical"] = new OverRide(),
            ["CabooseStationaryGuard"] = new OverRide(),
            ["SewerBPatrol1"] = new OverRide(),
            ["SewerAPatrol3"] = new OverRide(),
            ["SewerAPatrol2"] = new OverRide(),
            ["SewerAPatrol1"] = new OverRide(),
            ["RoofPatrolGreen"] = new OverRide(),
            ["RoofPatrolYellow"] = new OverRide(),
            ["StationaryPoint3"] = new OverRide(),
            ["StationaryPoint2"] = new OverRide(),
            ["StationaryPoint1"] = new OverRide(),
            ["GroundPatrolCyan"] = new OverRide(),
            ["GroundPatrolYellow"] = new OverRide(),
            ["GroundPatrolPurple"] = new OverRide(),
            ["StationaryPoint4 (16)"] = new OverRide(),
            ["StationaryPoint4 (13)"] = new OverRide(),
            ["StationaryPoint4 (5)"] = new OverRide(),
            ["StationaryPoint4 (4)"] = new OverRide(),
            ["StationaryPoint4 (3)"] = new OverRide(),
            ["StationaryPoint4 (1)"] = new OverRide(),
            ["StationaryPoint3 (2)"] = new OverRide(),
            ["StationaryPoint3 (1)"] = new OverRide(),
            ["StationaryPoint7"] = new OverRide(),
            ["StationaryPoint6"] = new OverRide(),
            ["ScientistSpawner (6)"] = new OverRide(),
            ["ScientistSpawner (5)"] = new OverRide(),
            ["ScientistSpawner (4)"] = new OverRide(),
            ["ScientistSpawner (3)"] = new OverRide(),
            ["ScientistSpawner (2)"] = new OverRide(),
            ["ScientistSpawner_Bunker"] = new OverRide(),
            ["ScientistSpawner_L2Main"] = new OverRide(),
            ["ScientistSpawner (1)"] = new OverRide(),
            ["RoofTop_2"] = new OverRide(),
            ["RoofTop"] = new OverRide(),
            ["L2-3"] = new OverRide(),
            ["L0_2"] = new OverRide(),
            ["L0"] = new OverRide(),
            ["ScientistSpawnerRoam"] = new OverRide(),
            ["ScientistSpawnerPatrolMainPath"] = new OverRide(),
            ["ScientistSpawnerRoamTethered"] = new OverRide(),
            ["ScientistSpawnerPatrol (1)"] = new OverRide(),
            ["ScientistSpawnerPatrol (2)"] = new OverRide(),
            ["ScientistSpawnerPatrol (3)"] = new OverRide(),
            ["ScientistSpawnerPatrol (4)"] = new OverRide(),
            ["ScientistSpawnerPatrol (5)"] = new OverRide(),
        };

        private static Hash<SpawnGroup, bool> _groups = new Hash<SpawnGroup, bool>();
        private HashSet<Data> _restore = new HashSet<Data>();
        private class Data
        {
            public SpawnGroup _group;
            public int _originalMin;
            public int _originalMax;
            public float _originalRespawnMin;
            public float _originalRespawnMax;

            public void Disable(SpawnGroup group)
            {
                _group = group;
                _originalMin = group.numToSpawnPerTickMin;
                _originalMax = group.numToSpawnPerTickMax;
                _originalRespawnMin = group.respawnDelayMin;
                _originalRespawnMax = group.respawnDelayMax;
                group.CancelInvoke(nameof(SpawnGroup.Spawn));
                group.CancelInvoke(nameof(SpawnGroup.SpawnRepeating));
                if (_group.WantsTimedSpawn()) _group.spawnClock.events.Clear();
                group.numToSpawnPerTickMin = group.maxPopulation;
                group.numToSpawnPerTickMax = group.maxPopulation;
                group.respawnDelayMin = float.PositiveInfinity;
                group.respawnDelayMax = float.PositiveInfinity;
            }

            public void RestoreVanilla()
            {
                if (_group == null) return;
                _group.numToSpawnPerTickMin = _originalMin;
                _group.numToSpawnPerTickMax = _originalMax;
                _group.respawnDelayMin = _originalRespawnMin;
                _group.respawnDelayMax = _originalRespawnMax;
                if (!_group.WantsTimedSpawn()) return;
                _group.spawnClock.events.Clear();
                _group.spawnClock.Add(_group.GetSpawnDelta(), _group.GetSpawnVariance(), _group.Spawn);
            }
        }

        private bool IsEnabled(string name)
        {
            if (string.IsNullOrEmpty(name)) return false;
            return _config.RespawnGroups.ContainsKey(name);
        }

        private bool TryGetSpawnTiming(SpawnGroup group, out float delta, out float variance)
        {
            delta = 0f;
            variance = 0f;
            float min = group.respawnDelayMin;
            float max = group.respawnDelayMax;
            if (float.IsNaN(min) || float.IsInfinity(min) || float.IsNaN(max) || float.IsInfinity(max))
            {
                //PrintError($"Invalid respawn delays for '{group.name}': " + $"Min={min:R}, Max={max:R}");
                return false;
            }
            float playerScale = SpawnHandler.PlayerScale(ConVar.Spawn.player_scale);
            if (float.IsNaN(playerScale) || float.IsInfinity(playerScale) || playerScale <= 0f)
            {
                //PrintError($"Invalid player scale for '{group.name}': " + $"PlayerScale={playerScale:R}");
                return false;
            }
            delta = ((min + max) * 0.5f) / playerScale;
            variance = ((max - min) * 0.5f) / playerScale;
            if (float.IsNaN(delta) || float.IsInfinity(delta) || float.IsNaN(variance) || float.IsInfinity(variance))
            {
                //PrintError($"Invalid calculated spawn timing for '{group.name}': " + $"Min={min:R}, Max={max:R}, " + $"PlayerScale={playerScale:R}, " + $"Delta={delta:R}, Variance={variance:R}");
                //delta = 300f;
                //variance = 0f;
                return false;
            }
            if (variance < 0f) variance = -variance;
            return true;
        }

        #endregion

        #region Config

        private static PluginConfig _config;

        private class PluginConfig
        {
            [JsonProperty("Drop Loot")]
            public bool DropLoot = false;

            [JsonProperty("Toggle Timed Spawn Groups true/false to override them & set a custom respawn time")]
            public Dictionary<string, OverRide> SpawnGroups = new Dictionary<string, OverRide>();

            [JsonProperty("Toggle NPC Timed Spawn Groups true/false to override them & set a custom respawn time")]
            public Dictionary<string, OverRide> NPCSpawnGroups = new Dictionary<string, OverRide>();

            [JsonIgnore]
            public Dictionary<string, int> RespawnGroups = new Dictionary<string, int>();
        }

        private class OverRide
        {
            [JsonProperty("Override Vanilla Respawn Time")]
            public bool OverrideRespawnTime = false;
            [JsonProperty("Set a Respawn Time (seconds)")]
            public int SpawnTime = 0;
        }

        protected override void LoadDefaultConfig()
        {
            _config = new PluginConfig();
            _config.SpawnGroups = _spawnGroups;
            _config.NPCSpawnGroups = _npcSpawnGroups;

            SaveConfig();
        }

        protected override void LoadConfig()
        {
            base.LoadConfig();

            try
            {
                _config = Config.ReadObject<PluginConfig>();
                if (_config == null) throw new FileNotFoundException();
            }
            catch (FileNotFoundException)
            {
                Puts($"No {Name} configuration file found, creating new config.");
                LoadDefaultConfig();
                SaveConfig();
            }
            catch (Exception ex)
            {
                PrintError("Failed to load config file (is the config file corrupt?) (" + ex.Message + ")");
                PrintError("Please verify your config file at https://jsonlint.com/");
            }
        }

        protected override void SaveConfig() => Config.WriteObject(_config, true);

        private static SpawnHandler spawnHandler = null;
        private void BuildConfig()
        {
            SpawnGroup[] groups = UnityEngine.Object.FindObjectsOfType<SpawnGroup>();
            int modified = 0;
            foreach (var group in groups)
            {
                //spawnGroup?.Fill();
                if (group == null || !group.isSpawnerActive || group.prefabs == null || group.prefabs.Count == 0) continue;
                if (_config.SpawnGroups.TryGetValue(group.name, out var value))
                {
                    if (value.SpawnTime == 0)
                    {
                        if (!TryGetSpawnTiming(group, out float delta, out float variance)) continue;
                        float random = delta + UnityEngine.Random.Range(-variance, variance);
                        if (float.IsNaN(random) || float.IsInfinity(random)) continue;
                        _config.SpawnGroups[group.name].SpawnTime = (int)random;
                    }
                    if (value.OverrideRespawnTime) _config.RespawnGroups.TryAdd(group.name, value.SpawnTime);
                }
                if (_config.NPCSpawnGroups.TryGetValue(group.name, out var npc))
                {
                    if (npc.SpawnTime == 0)
                    {
                        if (!TryGetSpawnTiming(group, out float delta, out float variance)) continue;
                        float random = delta + UnityEngine.Random.Range(-variance, variance);
                        if (float.IsNaN(random) || float.IsInfinity(random)) continue;
                        _config.NPCSpawnGroups[group.name].SpawnTime = (int)random;
                    }
                    if (npc.OverrideRespawnTime) _config.RespawnGroups.TryAdd(group.name, npc.SpawnTime);
                }

                if (!IsEnabled(group.name)) continue;
                if (!_groups.TryAdd(group, false)) continue;
                RunSpawn(group);
                Data d = new Data();
                d.Disable(group);
                _restore.Add(d);
                modified++;
            }

            SaveConfig();
            Puts($"Modified {modified}x spawn groups");
            spawnHandler = SingletonComponent<SpawnHandler>.Instance;
        }

        private const string DiveSiteName = "divesite";
        private const string DiveSitesName = "divesites";

        private void OnServerInitialized()
        {
            List<SpawnPopulationBase> new_spawns = new List<SpawnPopulationBase>();
            foreach (SpawnPopulationBase spawner in SpawnHandler.Instance.AllSpawnPopulations)
            {
                if (spawner.Prefabs == null) continue;
                foreach (Prefab<Spawnable> prefab in spawner.Prefabs) 
                    if (prefab.Name.Contains(DiveSiteName))
                    {
                        spawner.DeleteEntities();
                        spawner.Prefabs = null;
                        Puts("removing dive sites");
                    }else new_spawns.Add(spawner);
            }

            SpawnHandler.Instance.AllSpawnPopulations = new_spawns.ToArray();

            var handler = SingletonComponent<SpawnHandler>.Instance;
            if (handler == null) return;
            var populations = handler.AllSpawnPopulations;
            if (populations == null) return;
            for (int i = 0; i < populations.Length; i++)
            {
                var pop = populations[i];
                if (pop == null) continue;
                //Puts($"? {pop.name}");
                if (string.IsNullOrEmpty(pop.name) || (pop.name.IndexOf(DiveSiteName, StringComparison.OrdinalIgnoreCase) < 0 && pop.name.IndexOf(DiveSitesName, StringComparison.OrdinalIgnoreCase) < 0)) continue;
                Puts("error removing dive site");
                pop.DeleteEntities();
                pop.Prefabs = null;
            }

            Unsubscribe(nameof(OnLootEntityEnd));

            BuildConfig();

            if (_config.DropLoot) Subscribe(nameof(OnLootEntityEnd));
        }

        private void Unload()
        {
            foreach (var spawn in _restore) spawn.RestoreVanilla();

            Puts($"Restored {_restore.Count} spawn groups");
            _config.RespawnGroups.Clear();
            _restore.Clear();
            _groups.Clear();
            spawnHandler = null;
            _config = null;
        }

        #endregion

        #region Core

        [AutoPatch]
        [HarmonyPatch(typeof(SpawnGroup), nameof(SpawnGroup.ObjectRetired))]
        private static class SpawnGroup_ObjectRetired_Patch
        {
            private static void Prefix(SpawnGroup __instance, SpawnPointInstance instance)
            {
                if (__instance == null) return;
                if (!_groups.TryGetValue(__instance, out bool value)) return;
                if (value) return;
                _groups[__instance] = true;
                __instance.Invoke(() => RunSpawn(__instance), UnityEngine.Random.Range(_config.RespawnGroups[__instance.name] - 30, _config.RespawnGroups[__instance.name] + 1));
            }
        }

        private void OnLootEntityEnd(BasePlayer player, LootContainer instance)
        {
            if (player == null || instance == null) return;
            if (instance.inventory?.itemList?.Count > 0 && instance.HasBeenLooted) instance.DropItems();
        }

        const int MaxPopulation = 10;
        private static readonly FieldInfo SpawnPointInstanceEntity = typeof(SpawnPointInstance).GetField("Entity", BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public);
        private static void RunSpawn(SpawnGroup group)
        {
            if (group == null) return;
            //group.maxPopulation = 10;
            int safety = 0;
            while (group.currentPopulation < MaxPopulation)
            {
                if (++safety > MaxPopulation * 2)
                {
                    _groups[group] = false;
                    break;
                }
                GameObjectRef prefab = GetPrefab(group);
                if (prefab == null || string.IsNullOrEmpty(prefab.guid)) break;
                Vector3 pos;
                Quaternion rot;
                BaseSpawnPoint spawnPoint = GetSpawnPoint(group, prefab, out pos, out rot);
                if (spawnPoint == null) continue;
                BaseEntity entity = GameManager.server.CreateEntity(prefab.resourcePath, pos, rot, false);
                if (entity == null) continue;
                if (entity.enableSaving && group.shouldBlockSpawnedEntitySaving && !(spawnPoint is SpaceCheckingSpawnPoint)) entity.enableSaving = false;
                entity.gameObject.AwakeFromInstantiate();
                entity.Spawn();
                PostSpawnProcess(entity, spawnPoint);
                SpawnPointInstance instance = entity.gameObject.AddComponent<SpawnPointInstance>();
                instance.parentSpawnPointUser = group;
                instance.parentSpawnPoint = spawnPoint;
                SpawnPointInstanceEntity?.SetValue(instance, entity);
                //typeof(SpawnPointInstance).GetField("Entity", BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public)?.SetValue(instance, entity);
                instance.Notify();
            }

            _groups[group] = false;
        }

        private static GameObjectRef GetPrefab(SpawnGroup group)
        {
            int totalWeight = 0;
            for (int i = 0; i < group.prefabs.Count; i++)
            {
                var entry = group.prefabs[i];
                if (!group.preventDuplicates || !group.HasSpawned(entry.prefab.resourceID)) totalWeight += entry.weight;
            }

            if (totalWeight <= 0) return null;
            int roll = Random.Range(0, totalWeight);
            for (int i = 0; i < group.prefabs.Count; i++)
            {
                var entry = group.prefabs[i];
                if (group.preventDuplicates && group.HasSpawned(entry.prefab.resourceID)) continue;
                roll -= entry.weight;
                if (roll < 0) return entry.prefab;
            }

            return null;
        }

        /*private static GameObjectRef GetPrefab(SpawnGroup group)
        {
            float maxInclusive = (float) group.prefabs.Sum<SpawnGroup.SpawnEntry>((Func<SpawnGroup.SpawnEntry, int>) (x => !group.preventDuplicates || !group.HasSpawned(x.prefab.resourceID) ? x.weight : 0));
            if ((double) maxInclusive == 0.0) return null;
            float num = Random.Range(0.0f, maxInclusive);
            foreach (SpawnGroup.SpawnEntry prefab in group.prefabs)
            {
                int weight = !group.preventDuplicates || !group.HasSpawned(prefab.prefab.resourceID) ? prefab.weight : 0;
                if ((double) (num -= (float) weight) <= 0.0) return prefab.prefab;
            }
            return group.prefabs[group.prefabs.Count - 1].prefab;
        }*/

        private static BaseSpawnPoint GetSpawnPoint(SpawnGroup group, GameObjectRef prefabRef, out Vector3 pos, out Quaternion rot)
        {
            pos = Vector3.zero;
            rot = Quaternion.identity;
            BaseSpawnPoint[] points = group.spawnPoints;
            if (points == null || points.Length == 0) return null;
            int start = Random.Range(0, points.Length);
            for (int i = 0; i < points.Length; i++)
            {
                int index = start + i;
                if (index >= points.Length) index -= points.Length;
                BaseSpawnPoint spawnPoint = points[index];
                if (spawnPoint == null || !spawnPoint.IsAvailableTo(prefabRef.Get())) continue;
                spawnPoint.GetLocation(out pos, out rot);
                return spawnPoint;
            }

            return null;
        }

        /*private static BaseSpawnPoint GetSpawnPoint(SpawnGroup group, GameObjectRef prefabRef, out Vector3 pos, out Quaternion rot)
        {
            pos = Vector3.zero;
            rot = Quaternion.identity;
            int num = Random.Range(0, group.spawnPoints.Length);
            for (int index = 0; index < group.spawnPoints.Length; ++index)
            {
                BaseSpawnPoint spawnPoint = group.spawnPoints[(num + index) % group.spawnPoints.Length];
                if (!(spawnPoint == null) && spawnPoint.IsAvailableTo(prefabRef.Get()))
                {
                    spawnPoint.GetLocation(out pos, out rot);
                    return spawnPoint;
                }
            }
            return null;
        }*/

        private static void PostSpawnProcess(BaseEntity entity, BaseSpawnPoint spawnPoint)
        {
            if (!(entity is HumanNPC humanNpc)) return;
            if (spawnHandler == null || spawnHandler.JungleLoadouts == null || spawnHandler.JungleLoadouts.Length == 0) return;
            Vector3 position = spawnPoint.transform.position;
            if (TerrainMeta.BiomeMap.GetBiomeMaxType(position) != 16) return;
            if (EnvironmentManager.Check(position, EnvironmentType.TrainTunnels | EnvironmentType.UnderwaterLab | EnvironmentType.Submarine)) return;
            if (TerrainMeta.TopologyMap.GetTopology(position, 128)) return;
            humanNpc.EquipLoadout(spawnHandler.JungleLoadouts);
        }

        #endregion

    }
}