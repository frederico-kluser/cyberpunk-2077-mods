module DesertEagle

// Configuração do mod Desert Eagle.
// Os registos TweakDB são definidos declarativamente em src/tweakxl/desert_eagle.yaml;
// este ficheiro só expõe constantes usadas pelo código Redscript.
public class DesertEagleConfig {

  // ID TweakDB do item — tem de coincidir com a chave em src/tweakxl/desert_eagle.yaml.
  public static func ItemTDBID() -> TweakDBID {
    return t"Items.DesertEagle";
  }

  // Quantidade entregue por DesertEagleInventory.Give() quando não é indicada.
  public static func DefaultCount() -> Int32 {
    return 1;
  }

  // Sufixo visual da aparência por omissão (ver visualTags no .app/.xl).
  public static func DefaultVisualTag() -> CName {
    return n"DesertEagleDefault";
  }
}
