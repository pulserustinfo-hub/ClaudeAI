using System;
using System.Collections.Generic;
using System.Reflection;
using System.Reflection.Emit;
using HarmonyLib;
using Newtonsoft.Json;
using Oxide.Core;
using Oxide.Core.Plugins;
using UnityEngine;

namespace Oxide.Plugins
{

    [Info("PulseInstantCraft", "Mevent.Team", "2.2.1")]
    public class PulseInstantCraft : RustPlugin
    {
        #region Fields

        private static PulseInstantCraft _instance;
        private static Configuration _config;

        private const float NOTIFY_COOLDOWN = 3f;

        private readonly Dictionary<ulong, float> _lastFullNotify = new();

        #endregion

        #region Configuration

        protected override void LoadDefaultConfig()
        {
            _config = Configuration.DefaultConfig();
        }

        protected override void LoadConfig()
        {
            base.LoadConfig();
            try
            {
                _config = Config.ReadObject<Configuration>();
                if (_config == null) throw new Exception("config is null");
                _config.PluginVersion = Version;
                SaveConfig();
            }
            catch (Exception e)
            {
                PrintError($"Error loading config: {e.Message}");
                LoadDefaultConfig();
                Debug.LogException(e);
            }
        }

        protected override void SaveConfig()
        {
            Config.WriteObject(_config);
        }

        private class Configuration
        {
            [JsonProperty("Default crafting rate percentage")]
            public float CraftingRate;

            [JsonProperty("Default mixing rate percentage")]
            public float MixingRate;

            [JsonProperty("Allow crafting when inventory is full")]
            public bool AllowFullInventory = false;

            [JsonProperty("Config version")] public VersionNumber PluginVersion;

            public static Configuration DefaultConfig()
            {
                return new Configuration
                {
                    CraftingRate = 0.0f,
                    MixingRate = 0.0f,
                    AllowFullInventory = false,
                    PluginVersion = new VersionNumber()
                };
            }
        }

        #endregion

        #region Hooks

        private void Init()
        {
            _instance = this;
        }

        private void Unload()
        {
            _instance = null;
            _config = null;
        }

        private void OnPlayerDisconnected(BasePlayer player)
        {
            if (player == null) return;
            _lastFullNotify.Remove(player.userID);
        }

        #endregion

        #region Harmony Patches

        [AutoPatch]
        [HarmonyPatch(typeof(ItemCrafter), nameof(ItemCrafter.GetScaledDuration))]
        private static class GetScaledDurationPatch
        {
            private static void Postfix(ref float __result)
            {
                if (_config is null) return;
                __result *= _config.CraftingRate;
            }
        }

        [AutoPatch]
        [HarmonyPatch(typeof(ItemCrafter), nameof(ItemCrafter.CanCraft), typeof(ItemBlueprint), typeof(int), typeof(bool))]
        private static class CanCraftPatch
        {
            private static void Postfix(ItemCrafter __instance, ItemBlueprint bp, int amount, bool free, ref bool __result)
            {
                if (!__result || _config is null || _config.AllowFullInventory) return;
                if (WillOutputFit(__instance, bp, amount, free)) return;

                __result = false;
                _instance?.NotifyFull(__instance.owner);
            }
        }

        [AutoPatch]
        [HarmonyPatch(typeof(ItemCrafter), nameof(ItemCrafter.CraftItem))]
        private static class CraftItemPatch
        {
            private static void Prefix(ItemCrafter __instance, out int __state)
            {
                __state = __instance.queue.Count;
            }

            private static void Postfix(ItemCrafter __instance, bool __result, int __state)
            {
                if (!__result || _config is null || _config.CraftingRate > 0f) return;
                if (__instance.queue.Count <= __state) return;

                var task = __instance.queue.Last?.Value;
                if (task == null || IsTaskCancelled(task)) return;

                var owner = __instance.owner;
                if (owner == null) return;

                task.workbenchEntity = owner.GetCachedCraftLevelWorkbench();

                var amount = task.amount * task.blueprint.amountToCreate;

                var skin = ItemDefinition.FindSkin(task.blueprint.targetItem.itemid, task.skinID);

                var item = ItemManager.CreateByItemID(task.blueprint.targetItem.itemid, amount, skin);
                if (item == null)
                {
                    _instance.PrintError($"Exception creating item! targetItem: {task.blueprint.targetItem}-{amount}-{skin};");
                    return;
                }

                if (item.hasCondition && task.conditionScale != 1f)
                {
                    item.maxCondition *= task.conditionScale;
                    item.condition = item.maxCondition;
                }

                item.OnVirginSpawn(owner);
                item.SetItemOwnership(owner, ItemOwnershipPhrases.CraftedPhrase);

                if (task.instanceData != null) item.instanceData = task.instanceData;

                Interface.CallHook("OnItemCraftFinished", task, item, owner.inventory.crafting);

                var delivered = false;
                if (owner.inventory.GiveItem(item))
                {
                    owner.Command("note.inv", item.info.itemid, amount);
                    delivered = true;
                }
                else if (owner.inventory.crafting.containers.Count > 0)
                {
                    var itemContainer = owner.inventory.crafting.containers[0];
                    owner.Command("note.inv", item.info.itemid, item.amount);
                    owner.Command("note.inv", item.info.itemid, -item.amount);
                    item.Drop(itemContainer.dropPosition, itemContainer.dropVelocity);
                    delivered = true;
                }

                if (!delivered) return;

                __instance.queue.Remove(task);
                SetTaskCancelled(task);
                owner.Command("note.craft_done", task.taskUID, 0);
            }
        }

        [AutoPatch]
        [HarmonyPatch(typeof(MixingTable), nameof(MixingTable.StartMixing))]
        private static class MixingTableStartMixingPatch
        {
            private static IEnumerable<CodeInstruction> Transpiler(IEnumerable<CodeInstruction> instructions)
            {
                var injected = false;
                foreach (var instruction in instructions)
                {
                    if (!injected && instruction.Calls(
                            AccessTools.PropertySetter(typeof(MixingTable), nameof(MixingTable.RemainingMixTime))))
                    {
                        yield return new CodeInstruction(OpCodes.Call,
                            AccessTools.Method(typeof(MixingTableStartMixingPatch), nameof(ScaleDuration)));
                        injected = true;
                    }
                    yield return instruction;
                }

                if (!injected)
                    _instance?.PrintWarning("MixingTable.StartMixing transpiler: set_RemainingMixTime call not found: MixingRate scaling disabled. Likely a Rust update changed the IL. Plugin still works for crafting.");
            }

            private static float ScaleDuration(float duration)
            {
                var cfg = _config;
                if (cfg is null) return duration;

                var rate = cfg.MixingRate;
                if (float.IsNaN(rate) || float.IsInfinity(rate)) return duration;
                if (rate < 0f) rate = 0f;
                return duration * rate;
            }
        }

        #endregion

        #region Utils

        // Rust removed/renamed the public ItemCraftTask.cancelled field. Resolve the flag
        // via reflection so the plugin compiles regardless of what it is called now.
        private static readonly string[] CancelledMemberNames =
            { "cancelled", "Cancelled", "canceled", "Canceled", "isCancelled", "IsCancelled", "IsCanceled" };

        private static bool _cancelledLookupDone;
        private static FieldInfo _cancelledField;
        private static PropertyInfo _cancelledProperty;

        private static void ResolveCancelledMember()
        {
            if (_cancelledLookupDone) return;
            _cancelledLookupDone = true;

            const BindingFlags flags = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
            var type = typeof(ItemCraftTask);
            foreach (var name in CancelledMemberNames)
            {
                var field = type.GetField(name, flags);
                if (field != null && field.FieldType == typeof(bool))
                {
                    _cancelledField = field;
                    return;
                }

                var property = type.GetProperty(name, flags);
                if (property != null && property.PropertyType == typeof(bool))
                {
                    _cancelledProperty = property;
                    return;
                }
            }
        }

        private static bool IsTaskCancelled(ItemCraftTask task)
        {
            ResolveCancelledMember();
            if (_cancelledField != null) return (bool)_cancelledField.GetValue(task);
            if (_cancelledProperty != null && _cancelledProperty.CanRead) return (bool)_cancelledProperty.GetValue(task);
            return false;
        }

        private static void SetTaskCancelled(ItemCraftTask task)
        {
            ResolveCancelledMember();
            if (_cancelledField != null) _cancelledField.SetValue(task, true);
            else if (_cancelledProperty != null && _cancelledProperty.CanWrite) _cancelledProperty.SetValue(task, true);
        }

        private static bool WillOutputFit(ItemCrafter crafter, ItemBlueprint bp, int amount, bool free)
        {
            var inventory = crafter.owner?.inventory;
            var main = inventory?.containerMain;
            var belt = inventory?.containerBelt;
            if (main == null || belt == null) return true;

            var output = bp.targetItem;
            var outputStackSize = output.stackable;
            if (outputStackSize < 1) outputStackSize = 1;

            var capacity = ContainerOutputCapacity(main, output.itemid, outputStackSize)
                           + ContainerOutputCapacity(belt, output.itemid, outputStackSize);

            if (!free)
            {
                var ingredients = bp.GetIngredients();
                for (var i = 0; i < ingredients.Count; i++)
                {
                    var ingredient = ingredients[i];
                    if (ingredient.itemid == output.itemid) continue;

                    var needed = (int)ingredient.amount * amount;
                    var freed = ContainerFullStacksDrained(main, ingredient.itemid, ref needed)
                                + ContainerFullStacksDrained(belt, ingredient.itemid, ref needed);
                    capacity += (long)freed * outputStackSize;
                }
            }

            return capacity >= (long)amount * bp.amountToCreate;
        }

        private static long ContainerOutputCapacity(ItemContainer container, int outputItemId, int stackSize)
        {
            var empty = container.capacity - container.itemList.Count;
            var capacity = empty > 0 ? (long)empty * stackSize : 0L;

            var list = container.itemList;
            for (var i = 0; i < list.Count; i++)
            {
                var item = list[i];
                if (item.info.itemid != outputItemId) continue;

                var room = stackSize - item.amount;
                if (room > 0) capacity += room;
            }

            return capacity;
        }

        private static int ContainerFullStacksDrained(ItemContainer container, int itemId, ref int needed)
        {
            if (needed <= 0) return 0;

            var freed = 0;
            var list = container.itemList;
            for (var i = 0; i < list.Count; i++)
            {
                var item = list[i];
                if (item.info.itemid != itemId) continue;

                if (item.amount <= needed)
                {
                    needed -= item.amount;
                    freed++;
                    if (needed <= 0) break;
                }
                else
                {
                    needed = 0;
                    break;
                }
            }

            return freed;
        }

        private void NotifyFull(BasePlayer player)
        {
            if (player == null) return;

            var message = GetMsg("InventoryFull", player.UserIDString);
            if (string.IsNullOrEmpty(message)) return;

            var now = UnityEngine.Time.realtimeSinceStartup;
            if (_lastFullNotify.TryGetValue(player.userID, out var last) && now - last < NOTIFY_COOLDOWN) return;

            _lastFullNotify[player.userID] = now;
            player.ChatMessage(message);
        }

        #endregion

        #region Lang

        protected override void LoadDefaultMessages()
        {
            lang.RegisterMessages(new Dictionary<string, string>
            {
                ["InventoryFull"] = "You can't craft this - your inventory is full."
            }, this);
        }

        private string GetMsg(string key, string userId)
        {
            return lang.GetMessage(key, this, userId);
        }

        #endregion
    }
}

