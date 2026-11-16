/**
 * Validação de CPF e CNPJ (numérico e alfanumérico) — JavaScript/TypeScript (sem dependências)
 * Regra do CNPJ alfanumérico: valor = código ASCII - 48, módulo 11 (IN RFB 2.229/2024).
 */
const limpar = (doc) => String(doc ?? '').replace(/[.\-\/\s]/g, '').toUpperCase();
const mod11 = (soma) => { const r = soma % 11; return r < 2 ? 0 : 11 - r; };

function cnpjDV(base12) {
  const b = limpar(base12);
  if (!/^[A-Z0-9]{12}$/.test(b)) throw new Error('Base do CNPJ precisa ter 12 caracteres (0-9 ou A-Z)');
  const p1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
  const p2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
  const val = (c) => c.charCodeAt(0) - 48;
  const dv1 = mod11([...b].reduce((s, c, i) => s + val(c) * p1[i], 0));
  const dv2 = mod11([...(b + dv1)].reduce((s, c, i) => s + val(c) * p2[i], 0));
  return `${dv1}${dv2}`;
}

function cnpjValido(cnpj) {
  const c = limpar(cnpj);
  if (!/^[A-Z0-9]{12}[0-9]{2}$/.test(c)) return false;
  if (new Set(c).size === 1) return false;
  return cnpjDV(c.slice(0, 12)) === c.slice(12);
}

function cpfValido(cpf) {
  const c = limpar(cpf);
  if (!/^[0-9]{11}$/.test(c) || new Set(c).size === 1) return false;
  for (let t = 9; t < 11; t++) {
    let soma = 0;
    for (let i = 0; i < t; i++) soma += Number(c[i]) * (t + 1 - i);
    if (mod11(soma) !== Number(c[t])) return false;
  }
  return true;
}

module.exports = { limpar, cnpjDV, cnpjValido, cpfValido };
