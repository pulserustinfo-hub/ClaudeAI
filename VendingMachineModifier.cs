using HarmonyLib;
using System;
using System.IO;
using System.Linq;
using System.Collections;
using System.Collections.Generic;
using Newtonsoft.Json;
using Oxide.Core;
using Oxide.Core.Plugins;
using Rust;
using UnityEngine;

namespace Oxide.Plugins
{
    [Info("VendingMachineModifier","Khan","1.0.0")]
    [Description("Exports and applies custom vending machine sell orders with infinite stock & instant buy")]
    public class VendingMachineModifier : RustPlugin
    {

        private static PluginConfig _config;
        private class PluginConfig
        {
            public List<Machine> Machines = new List<Machine>();
            public Dictionary<string, object> ToDictionary() => JsonConvert.DeserializeObject<Dictionary<string, object>>(JsonConvert.SerializeObject(this));
        }

        private class Machine
        {
            public string PrefabName;
            public string Monument;
            public string ShopName;
            public Position Position;
            public List<OrderConfig> SellOrders;
        }

        private class Position
        {
            public float X;
            public float Y;
            public float Z;
        }

        private class OrderConfig
        {
            public string ItemToSell;
            public int ItemToSellAmount;
            public string Currency;
            public int CurrencyAmountPerItem;
            public bool ItemToSellIsBP;
            public bool CurrencyIsBP;
            public float ItemCondition;
            public float ItemConditionMax;
            public int InstanceData;
            public List<int> Attachments;
            public int TotalAttachmentSlots;
            public float PriceMultiplier;
            public int AmmoType;
            public int AmmoCount;
            public float ReceivedQuantityMultiplier;
            public ulong SellSkinId;
            public ulong CostSkinId;
        }

        protected override void LoadDefaultConfig()
        {
            _config = new PluginConfig();
            //var machines = BaseNetworkable.serverEntities.OfType<VendingMachine>();
            var machines = UnityEngine.Object.FindObjectsOfType<VendingMachine>();
            var generated = new List<Machine>(machines.Length);
            for (int i = 0; i < machines.Length; i++)
            {
                var machine = machines[i];
                if (machine == null || !machine.isServer) continue;
                var position = machine.transform.position;
                var entry = new Machine
                {
                    PrefabName = machine.ShortPrefabName,
                    Monument = GetMonumentName(machine.transform.position),
                    ShopName = machine.shopName,
                    Position = new Position
                    {
                        X = position.x,
                        Y = position.y,
                        Z = position.z
                    },
                    SellOrders = new List<OrderConfig>()
                };

                var orders = machine.sellOrders?.sellOrders;
                if (orders != null)
                {
                    for (int j = 0; j < orders.Count; j++)
                    {
                        var order = orders[j];
                        if (order == null) continue;
                        var item = ItemManager.FindItemDefinition(order.itemToSellID);
                        var currency = ItemManager.FindItemDefinition(order.currencyID);
                        entry.SellOrders.Add(new OrderConfig
                        {
                            ItemToSell = item?.shortname ?? order.itemToSellID.ToString(),
                            ItemToSellAmount = order.itemToSellAmount,
                            Currency = currency?.shortname ?? order.currencyID.ToString(),
                            CurrencyAmountPerItem = order.currencyAmountPerItem,
                            ItemToSellIsBP = order.itemToSellIsBP,
                            CurrencyIsBP = order.currencyIsBP,
                            ItemCondition = order.itemCondition,
                            ItemConditionMax = order.itemConditionMax,
                            InstanceData = order.instanceData,
                            Attachments = order.attachmentsList == null ? null : new List<int>(order.attachmentsList),
                            TotalAttachmentSlots = order.totalAttachmentSlots,
                            PriceMultiplier = order.priceMultiplier,
                            AmmoType = order.ammoType,
                            AmmoCount = order.ammoCount,
                            ReceivedQuantityMultiplier = order.receivedQuantityMultiplier,
                            SellSkinId = order.sellSkinId,
                            CostSkinId = order.costSkinId
                        });
                    }
                }

                generated.Add(entry);
            }

            _config.Machines = generated;
            Puts($"Generated vending configuration: {generated.Count} machines.");
            SaveConfig();
        }

        protected override void LoadConfig()
        {
            base.LoadConfig();

            try
            {
                _config = Config.ReadObject<PluginConfig>();
                if (_config == null) throw new FileNotFoundException();
                if (!_config.ToDictionary().Keys.SequenceEqual(Config.ToDictionary(x => x.Key, x => x.Value).Keys))
                {
                    PrintWarning("Configuration appears to be outdated; updating and saving");
                    SaveConfig();
                }
            }
            catch (FileNotFoundException)
            {
                PrintWarning($"No {Name} configuration file found, creating new config.");
                LoadDefaultConfig();
                SaveConfig();
            }
            catch (Exception ex)
            {
                PrintWarning("Failed to load config file (is the config file corrupt?) (" + ex.Message + ")");
                PrintError("Please verify your config file at https://jsonlint.com/");
            }
        }

        protected override void SaveConfig() => Config.WriteObject(_config, true);

        private void OnServerInitialized()
        {
            var machines = UnityEngine.Object.FindObjectsOfType<VendingMachine>();
            foreach (var machine in machines) Set(machine);
        }

        private void Unload()
        {
            _config = null;
        }

        object OnBuyVendingItem(VendingMachine machine, BasePlayer player, int sellOrderIdIndex, int numberOfTransactions)
        {
            if (machine?.sellOrders?.sellOrders == null || player == null) return null;
            int num = 0;
            var orders = machine.sellOrders.sellOrders;
            for (int i = 0; i < orders.Count; i++)
            {
                var order = orders[i];
                var itemDef = ItemManager.FindItemDefinition(order.itemToSellID);
                var currencyDef = ItemManager.FindItemDefinition(order.currencyID);
                if (itemDef == null || currencyDef == null || !itemDef.IsAllowed(machine.CurrentEraRestriction) || !currencyDef.IsAllowed(machine.CurrentEraRestriction)) continue;
                if (num++ != sellOrderIdIndex) continue;
                int maxItems = Space(player, itemDef);
                if (maxItems < order.itemToSellAmount)
                {
                    player.ShowToast(GameTip.Styles.Red_Normal, new Translate.Phrase("space", "You don't have enough inventory space to buy this item."), true);
                    return false;
                }
                int maxTransactions = maxItems / order.itemToSellAmount;
                if (numberOfTransactions > maxTransactions) numberOfTransactions = maxTransactions;
            }

            if (machine.HasVendingSounds()) machine.ClientRPC(RpcTarget.NetworkGroup("CLIENT_StartVendingSounds"), sellOrderIdIndex);
            machine.DoTransaction(player, sellOrderIdIndex, numberOfTransactions);
            return false;
        }

        private static int Space(BasePlayer player, ItemDefinition def)
        {
            if (player?.inventory == null || def == null) return 0;
            int stackLimit = def.stackable <= 0 ? 1 : def.stackable;
            int stackSpace = 0;
            int freeSlots = 0;
            List<ItemContainer> containers = Facepunch.Pool.Get<List<ItemContainer>>();
            var backpack = player.inventory.GetBackpackWithInventory()?.contents;
            containers.Add(player.inventory.containerMain);
            containers.Add(player.inventory.containerBelt);
            if (backpack != null) containers.Add(backpack);
            foreach (ItemContainer container in containers)
            {
                freeSlots += container.capacity - container.itemList.Count;
                foreach (Item item in container.itemList)
                {
                    if (item.info.itemid != def.itemid) continue;
                    int available = stackLimit - item.amount;
                    if (available > 0) stackSpace += available;
                }
            }
            Facepunch.Pool.Free(ref containers);
            int space = stackSpace + (freeSlots * stackLimit);
            return space;
        }

        [AutoPatch]
        [HarmonyPatch(typeof(VendingMachine), nameof(VendingMachine.OutOfStock))]
        private static class OutOfStockPatch
        {
            private static bool Prefix(VendingMachine __instance, ref bool __result)
            {
                __result = true;
                Set(__instance);
                return true;
            }
        }

        private static void Set(VendingMachine machine)
        {
            if (machine.OwnerID.IsSteamId()) return;
            foreach (ProtoBuf.VendingMachine.SellOrder sellOrder in machine.sellOrders.sellOrders) if (sellOrder.inStock != 999000000) sellOrder.inStock = 999000000;

            foreach (var item in machine.inventory.itemList)
                if (item.amount != 999000000)
                {
                    item.amount = 999000000;
                    item.MarkDirty();
                }
        }

        [ConsoleCommand("vending.update")]
        private void ApplyConfig(ConsoleSystem.Arg arg)
        {
            if (!HasPermission(arg))
            {
                arg.ReplyWith("You are not authorized to use this command.");
                return;
            }

            if (_config?.Machines == null || _config.Machines.Count == 0)
            {
                arg.ReplyWith("No vending machines found in the configuration.");
                return;
            }

            var machines = UnityEngine.Object.FindObjectsOfType<VendingMachine>();
            var applied = new HashSet<Machine>();
            int updated = 0;
            int skipped = 0;

            for (int i = 0; i < machines.Length; i++)
            {
                var machine = machines[i];
                if (machine == null || !machine.isServer /*|| machine.transactionActive*/) continue;

                var position = machine.transform.position;
                Machine match = null;
                float closestDistance = 0.25f;

                for (int j = 0; j < _config.Machines.Count; j++)
                {
                    var entry = _config.Machines[j];
                    if (entry == null || entry.Position == null || entry.SellOrders == null || applied.Contains(entry)) continue;
                    if (!string.Equals(machine.ShortPrefabName, entry.PrefabName, StringComparison.Ordinal)) continue;
                    float dx = position.x - entry.Position.X;
                    float dy = position.y - entry.Position.Y;
                    float dz = position.z - entry.Position.Z;
                    float distance = dx * dx + dy * dy + dz * dz;
                    if (distance <= closestDistance)
                    {
                        closestDistance = distance;
                        match = entry;
                    }
                }

                if (match == null) continue;
                if (match.SellOrders.Count > 7)
                {
                    PrintWarning($"Skipped {machine.ShortPrefabName}: more than 7 sell orders.");
                    skipped++;
                    continue;
                }

                var newOrders = new List<ProtoBuf.VendingMachine.SellOrder>(match.SellOrders.Count);
                bool valid = true;
                for (int j = 0; j < match.SellOrders.Count; j++)
                {
                    var saved = match.SellOrders[j];
                    if (saved == null || saved.ItemToSellAmount < 1 || saved.CurrencyAmountPerItem < 1 || saved.CurrencyAmountPerItem > 10000)
                    {
                        valid = false;
                        break;
                    }

                    var item = FindItem(saved.ItemToSell);
                    var currency = FindItem(saved.Currency);
                    if (item == null || currency == null)
                    {
                        PrintWarning($"Skipped {machine.ShortPrefabName}: invalid item or currency in order {j + 1}.");
                        valid = false;
                        break;
                    }

                    var order = new ProtoBuf.VendingMachine.SellOrder
                    {
                        ShouldPool = false,
                        itemToSellID = item.itemid,
                        itemToSellAmount = Mathf.Clamp(saved.ItemToSellAmount, 1, item.stackable),
                        currencyID = currency.itemid,
                        currencyAmountPerItem = Mathf.Clamp(saved.CurrencyAmountPerItem, 1, 10000),
                        itemToSellIsBP = saved.ItemToSellIsBP,
                        currencyIsBP = saved.CurrencyIsBP,
                        itemCondition = saved.ItemCondition,
                        itemConditionMax = saved.ItemConditionMax,
                        instanceData = saved.InstanceData,
                        attachmentsList = saved.Attachments == null ? null : new List<int>(saved.Attachments),
                        totalAttachmentSlots = saved.TotalAttachmentSlots,
                        priceMultiplier = saved.PriceMultiplier,
                        ammoType = saved.AmmoType,
                        ammoCount = saved.AmmoCount,
                        receivedQuantityMultiplier = saved.ReceivedQuantityMultiplier,
                        sellSkinId = saved.SellSkinId,
                        costSkinId = saved.CostSkinId
                    };

                    newOrders.Add(order);
                }

                if (!valid)
                {
                    skipped++;
                    continue;
                }

                if (machine.sellOrders == null)
                {
                    machine.sellOrders = new ProtoBuf.VendingMachine.SellOrderContainer
                    {
                        ShouldPool = false,
                        sellOrders = newOrders
                    };
                }
                else
                {
                    machine.sellOrders.sellOrders = newOrders;
                }

                machine.FullUpdate();
                machine.SendSellOrders();
                applied.Add(match);
                updated++;
            }

            Puts($"Vending configuration applied: {updated} updated, {skipped} skipped.");
            arg.ReplyWith($"Updated {updated} vending machines. Skipped {skipped}.");
        }

        private bool HasPermission(ConsoleSystem.Arg arg) => arg.Connection == null || arg.Connection.authLevel >= 2;
        private ItemDefinition FindItem(string value)
        {
            if (string.IsNullOrEmpty(value)) return null;
            var definition = ItemManager.FindItemDefinition(value);
            if (definition != null) return definition;
            int itemId;
            return int.TryParse(value, out itemId) ? ItemManager.FindItemDefinition(itemId) : null;
        }

        private string GetMonumentName(Vector3 position)
        {
            var monuments = TerrainMeta.Path.Monuments;
            if (monuments == null) return "Unknown";
            MonumentInfo closest = null;
            float closestDistance = float.MaxValue;
            foreach (var monument in monuments)
            {
                if (monument == null) continue;
                float distance = (monument.transform.position - position).sqrMagnitude;
                if (distance >= closestDistance) continue;
                closestDistance = distance;
                closest = monument;
            }

            return closest?.name ?? "Unknown";
        }

    }
}
