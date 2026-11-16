# Campos do Pix copia e cola (BR Code)

Formato de cada campo: `ID` (2) + `tamanho` (2, com zero à esquerda) + `valor`.

| ID | Nome | Valor no Pix | Obrigatório |
|---|---|---|---|
| 00 | Payload Format Indicator | `01` | Sim, sempre o primeiro |
| 01 | Point of Initiation Method | `12` = uso único (opcional; costuma aparecer em QR dinâmico) | Não |
| 26 | Merchant Account Information (Pix) | Grupo com os subcampos abaixo | Sim |
| 52 | Merchant Category Code | `0000` | Sim |
| 53 | Moeda | `986` (Real) | Sim |
| 54 | Valor | `12.50` (ponto, 2 casas) | Não |
| 58 | País | `BR` | Sim |
| 59 | Nome do recebedor | Até 25 caracteres | Sim |
| 60 | Cidade do recebedor | Até 15 caracteres | Sim |
| 62 | Additional Data Field | Grupo com o subcampo 05 (txid) | Sim |
| 63 | CRC16 | 4 hex maiúsculos, sempre o último | Sim |

**Subcampos do 26 (Pix)**

| ID | Conteúdo |
|---|---|
| 00 | GUI `br.gov.bcb.pix` |
| 01 | Chave Pix (QR estático) |
| 02 | Informação adicional/descrição (opcional) |
| 25 | URL do payload (QR dinâmico, sem `https://`) |

**Subcampo do 62**

| ID | Conteúdo |
|---|---|
| 05 | txid: no estático, até 25 caracteres alfanuméricos ou `***` |

## Exemplo oficial para teste

Exemplo do manual do Banco Central (chave aleatória, sem valor):

```
00020126580014br.gov.bcb.pix0136123e4567-e12b-12d1-a456-4266554400005204000053039865802BR5913Fulano de Tal6008BRASILIA62070503***63041D3D
```

Destrinchando:

```
00 02 01
26 58  00 14 br.gov.bcb.pix
       01 36 123e4567-e12b-12d1-a456-426655440000
52 04 0000
53 03 986
58 02 BR
59 13 Fulano de Tal
60 08 BRASILIA
62 07  05 03 ***
63 04 1D3D        <- CRC16 de tudo antes, incluindo "6304"
```

## CRC16 em outras linguagens

**PHP**
```php
function pix_crc16(string $payload): string {
    $crc = 0xFFFF;
    for ($i = 0, $n = strlen($payload); $i < $n; $i++) {
        $crc ^= ord($payload[$i]) << 8;
        for ($b = 0; $b < 8; $b++) {
            $crc = ($crc & 0x8000) ? (($crc << 1) ^ 0x1021) : ($crc << 1);
            $crc &= 0xFFFF;
        }
    }
    return strtoupper(str_pad(dechex($crc), 4, '0', STR_PAD_LEFT));
}
// uso: $codigo = $payloadSemCrc . '6304'; $codigo .= pix_crc16($codigo);
```

**JavaScript**
```js
function pixCrc16(payload) {
  let crc = 0xFFFF;
  for (const byte of new TextEncoder().encode(payload)) {
    crc ^= byte << 8;
    for (let b = 0; b < 8; b++) {
      crc = (crc & 0x8000) ? ((crc << 1) ^ 0x1021) : (crc << 1);
      crc &= 0xFFFF;
    }
  }
  return crc.toString(16).toUpperCase().padStart(4, '0');
}
```

## Erros comuns e o que significam

| Sintoma no app do banco | Causa provável |
|---|---|
| "QR Code inválido" logo na leitura | CRC errado, ou CRC calculado sem incluir `6304` |
| Lê, mas mostra outra chave/nome | Tamanho errado em algum campo, deslocando os seguintes |
| Rejeita só alguns apps | Acento ou caractere especial no nome/cidade, ou nome com mais de 25 caracteres |
| Valor aparece errado | Vírgula no lugar do ponto, ou separador de milhar |
