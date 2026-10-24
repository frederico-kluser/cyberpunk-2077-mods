module DesertEagle

// Helper de teste do mod Desert Eagle: entrega a arma ao jogador para validar
// em segundos todo o pipeline de assets (malha, entidade, aparências, animações).
//
// A entrada de inventário "Items.DesertEagle" é criada de forma aditiva pelo
// TweakXL em src/tweakxl/desert_eagle.yaml (não substitui nenhum ficheiro vanilla).
//
// Uso em jogo (Cyber Engine Tweaks):
//   Game.AddToInventory("Items.DesertEagle", 1)
// ou, a partir de outro script Redscript:
//   DesertEagleInventory.Give();
public class DesertEagleInventory {

  // Entrega a quantidade por omissão (DesertEagleConfig.DefaultCount).
  public static func Give() -> Bool {
    return DesertEagleInventory.Give(DesertEagleConfig.DefaultCount());
  }

  // Entrega `count` Desert Eagles ao jogador. Devolve false se a transação falhar
  // (por exemplo, quando o registo TweakDB ainda não está carregado).
  public static func Give(count: Int32) -> Bool {
    let player: ref<PlayerPuppet> = GetPlayer(GetGameInstance());
    let itemID: ItemID = ItemID.FromTDBID(DesertEagleConfig.ItemTDBID());
    let transactionSystem: ref<TransactionSystem> = GameInstance.GetTransactionSystem(GetGameInstance());
    return transactionSystem.GiveItem(player, itemID, count);
  }
}
