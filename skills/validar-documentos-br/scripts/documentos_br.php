<?php
/**
 * Validação de CPF e CNPJ (numérico e alfanumérico) — PHP 7.4+
 * Regra do CNPJ alfanumérico: valor = código ASCII - 48, módulo 11 (IN RFB 2.229/2024).
 */

function doc_limpar(string $doc): string {
    return strtoupper(preg_replace('/[.\-\/\s]/', '', $doc));
}

function doc_mod11(int $soma): int {
    $resto = $soma % 11;
    return $resto < 2 ? 0 : 11 - $resto;
}

function cnpj_dv(string $base12): string {
    $base12 = doc_limpar($base12);
    if (!preg_match('/^[A-Z0-9]{12}$/', $base12)) {
        throw new InvalidArgumentException('Base do CNPJ precisa ter 12 caracteres (0-9 ou A-Z)');
    }
    $p1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
    $p2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
    $soma = 0;
    for ($i = 0; $i < 12; $i++) { $soma += (ord($base12[$i]) - 48) * $p1[$i]; }
    $dv1 = doc_mod11($soma);
    $base13 = $base12 . $dv1;
    $soma = 0;
    for ($i = 0; $i < 13; $i++) { $soma += (ord($base13[$i]) - 48) * $p2[$i]; }
    return $dv1 . doc_mod11($soma);
}

function cnpj_valido(string $cnpj): bool {
    $c = doc_limpar($cnpj);
    if (!preg_match('/^[A-Z0-9]{12}[0-9]{2}$/', $c)) return false;
    if (count(array_unique(str_split($c))) === 1) return false;
    return cnpj_dv(substr($c, 0, 12)) === substr($c, 12, 2);
}

function cpf_valido(string $cpf): bool {
    $c = doc_limpar($cpf);
    if (!preg_match('/^[0-9]{11}$/', $c)) return false;
    if (count(array_unique(str_split($c))) === 1) return false;
    for ($t = 9; $t < 11; $t++) {
        $soma = 0;
        for ($i = 0; $i < $t; $i++) { $soma += (int)$c[$i] * (($t + 1) - $i); }
        if (doc_mod11($soma) !== (int)$c[$t]) return false;
    }
    return true;
}
