import re
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from docx import Document
from docx.text.paragraph import Paragraph
from docx.oxml import OxmlElement


class ValidadorDados:
    @staticmethod
    def validar_cpf(cpf):
        cpf = re.sub(r"\D", "", cpf)
        if len(cpf) != 11:
            raise ValueError(f"CPF inválido: deve ter 11 dígitos. Recebido: {cpf}")
        return cpf

    @staticmethod
    def validar_cnpj(cnpj):
        cnpj = re.sub(r"\D", "", cnpj)
        if len(cnpj) != 14:
            raise ValueError(f"CNPJ inválido: deve ter 14 dígitos. Recebido: {cnpj}")
        return cnpj

    @staticmethod
    def formatar_cpf(cpf):
        cpf = re.sub(r"\D", "", cpf)
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

    @staticmethod
    def formatar_cnpj(cnpj):
        cnpj = re.sub(r"\D", "", cnpj)
        return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"


class Gerador:
    TIPOS_LICENCA = {
        "1": "SMART de 01 a 02 equipos/Consultorios",
        "2": "Clinic de 01 a 02 equipos/Consultorios",
        "3": "Clinic de 03 a 04 equipos/Consultorios",
        "4": "Clinic de 05 a 08 equipos/Consultorios",
        "5": "Clinic de 09 a 12 equipos/Consultorios",
    }

    RANGES_EQUIPOS = {
        "1": (1, 2),
        "2": (1, 2),
        "3": (3, 4),
        "4": (5, 8),
        "5": (9, 12),
    }

    TIPOS_IMPLANTACAO = {
        "1": ["Smart", "Clinic"],
        "2": ["Clinic"],
    }

    TIPOS_MIGRACAO = {
        "0": "Isento",
        "1": "Padrão",
        "2": "Inteligente",
    }

    FORMATOS_PAGAMENTO = {
        "1": "Recorrente",
        "2": "Plano Integral no Cartão",
        "3": "PIX",
        "4": "Mensal",
    }

    TABELA_PRECOS = {
        "1": {
            "1": {1: 164.00, 2: 164.00},
            "2": {1: 149.00, 2: 149.00},
            "3": {1: 149.00, 2: 149.00},
            "4": {1: 276.00, 2: 276.00},
        },
        "2": {
            "1": {1: 249.00, 2: 249.00},
            "2": {1: 220.80, 2: 220.80},
            "3": {1: 220.80, 2: 220.80},
            "4": {1: 276.00, 2: 276.00},
        },
        "3": {
            "1": {3: 388.00, 4: 388.00},
            "2": {3: 345.60, 4: 345.60},
            "3": {3: 345.60, 4: 345.60},
            "4": {3: 432.00, 4: 432.00},
        },
        "4": {
            "1": {5: 569.00, 6: 569.00, 7: 569.00, 8: 569.00},
            "2": {5: 518.40, 6: 518.40, 7: 518.40, 8: 518.40},
            "3": {5: 518.40, 6: 518.40, 7: 518.40, 8: 518.40},
            "4": {5: 648.00, 6: 648.00, 7: 648.00, 8: 648.00},
        },
        "5": {
            "1": {9: 760.00, 10: 760.00, 11: 760.00, 12: 760.00},
            "2": {9: 691.20, 10: 691.20, 11: 691.20, 12: 691.20},
            "3": {9: 691.20, 10: 691.20, 11: 691.20, 12: 691.20},
            "4": {9: 864.00, 10: 864.00, 11: 864.00, 12: 864.00},
        },
    }

    TAXA_IMPLANTACAO = {
        "1": 490.00,
        "2": 490.00,
        "3": 490.00,
        "4": 490.00,
    }

    MIGRACAO_PADRAO_VALOR = 0.00
    MIGRACAO_INTELIGENTE_VALOR = 2500.00
    MIGRACAO_INTELIGENTE_PARCELAS = 12
    PRAZO_MIGRACAO_PADRAO = "10 a 15 dias úteis"
    PRAZO_MIGRACAO_INTELIGENTE = "30 a 45 dias"

    IMPLANTACAO_SMART_TEXTO = (
        "Smart | 1 treinamento ao vivo 1x por semana com horário pré definido, "
        "vídeos aulas liberados de forma ilimitada na plataforma. Além de suporte premium via chamado."
    )
    IMPLANTACAO_CLINIC_TEXTO = (
        "Clinic | Time de Onboard que disponibilizará 4 encontros ao vivo e personalizado, "
        "60 dias de acompanhamento, vídeos aulas ilimitados na plataforma, Gerente de contas "
        "e suporte premium via chamado."
    )

    DESCONTOS = {
        "0": 0.00,
        "1": 0.05,
        "2": 0.10,
        "3": 0.15,
        "4": 0.20,
    }

    def __init__(self):
        self.caminho_templates = Path("templates")
        self.caminho_saida = Path("contratos_gerados")
        self._criar_diretorios()

    def _criar_diretorios(self):
        self.caminho_templates.mkdir(exist_ok=True)
        self.caminho_saida.mkdir(exist_ok=True)

    def _mapear_template(self, tipo_licenca):
        candidatos = [
            self.caminho_templates / f"template_licenca_{tipo_licenca.lower()}.docx",
            self.caminho_templates / "template_licenca_básica.docx",
            self.caminho_templates / " template_licenca_equipos_pj.docx",
        ]

        for caminho in candidatos:
            if caminho.exists():
                return caminho

        raise FileNotFoundError("Nenhum template DOCX encontrado na pasta templates/")

    def _substituir_em_paragrafo(self, paragrafo, substituicoes):
        for chave, valor in substituicoes.items():
            valor = "" if valor is None else str(valor)
            if chave not in paragrafo.text:
                continue

            if paragrafo.text == chave:
                paragrafo.text = valor
                continue

            for run in paragrafo.runs:
                if chave in run.text:
                    run.text = run.text.replace(chave, valor)

    def _substituir_em_tabelas(self, doc, substituicoes):
        for tabela in doc.tables:
            for linha in tabela.rows:
                for celula in linha.cells:
                    for paragrafo in celula.paragraphs:
                        self._substituir_em_paragrafo(paragrafo, substituicoes)

    def _substituir_em_corpo(self, doc, substituicoes):
        for paragrafo in doc.paragraphs:
            self._substituir_em_paragrafo(paragrafo, substituicoes)

    def _inserir_depois(self, paragrafo, texto):
        novo_elemento = OxmlElement("w:p")
        paragrafo._p.addnext(novo_elemento)
        novo_paragrafo = Paragraph(novo_elemento, paragrafo._parent)
        novo_paragrafo.add_run(texto)
        return novo_paragrafo

    def _remover_paragrafo(self, paragrafo):
        elemento = paragrafo._element
        elemento.getparent().remove(elemento)
        paragrafo._p = paragrafo._element = None

    def _substituir_secao(self, doc, titulo_inicio, titulo_fim, linhas):
        paragrafos = list(doc.paragraphs)
        inicio = next((i for i, p in enumerate(paragrafos) if p.text.strip() == titulo_inicio), None)
        if inicio is None:
            return

        fim = len(paragrafos)
        if titulo_fim:
            fim = next((i for i, p in enumerate(paragrafos[inicio + 1:], inicio + 1) if p.text.strip() == titulo_fim), fim)

        for paragrafo in paragrafos[inicio + 1:fim]:
            self._remover_paragrafo(paragrafo)

        ancora = paragrafos[inicio]
        for linha in linhas:
            ancora = self._inserir_depois(ancora, linha)

    def _dinheiro(self, valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def calcular_valor_licenca(self, tipo_licenca_key, formato_pagamento_key, qtd_equipos):
        try:
            return self.TABELA_PRECOS[tipo_licenca_key][formato_pagamento_key][int(qtd_equipos)]
        except (KeyError, TypeError, ValueError):
            return 0.00

    def calcular_valor_final(self, valor_base, desconto_percentual):
        return valor_base - (valor_base * desconto_percentual)

    def _calcular_valores(self, tipo_licenca, formato_pagamento, qtd_equipos, desconto_percentual=0.0):
        formato_key = self._normalizar_formato_pagamento(formato_pagamento)
        valor_mensal_base = self.calcular_valor_licenca(tipo_licenca, formato_key, qtd_equipos)
        valor_mensal_final = self.calcular_valor_final(valor_mensal_base, desconto_percentual)

        valor_tabela_anual = self.calcular_valor_licenca(tipo_licenca, "1", qtd_equipos) * 12
        valor_total_anual = valor_mensal_final * 12

        return formato_key, valor_mensal_base, valor_mensal_final, valor_tabela_anual, valor_total_anual

    def _normalizar_formato_pagamento(self, formato_pagamento):
        if formato_pagamento in self.FORMATOS_PAGAMENTO:
            return formato_pagamento

        for chave, nome in self.FORMATOS_PAGAMENTO.items():
            if nome == formato_pagamento:
                return chave

        return "1"

    def _normalizar_migracao(self, tipo_migracao):
        texto = (tipo_migracao or "").strip().lower()
        if texto in {"0", "isento", "isenta", "sem migração", "sem migracao", "nenhuma"}:
            return "isento"
        if texto in {"2", "inteligente", "completa", "migração inteligente", "migração completa"}:
            return "inteligente"
        return "padrao"

    def _normalizar_implantacao(self, tipo_implantacao, tipo_licenca):
        if tipo_implantacao:
            return tipo_implantacao
        return "Smart" if tipo_licenca == "1" else "Clinic"

    def montar_clausula_financeira(
        self,
        tipo_licenca,
        formato_pagamento,
        qtd_equipos,
        desconto_percentual=0.0,
    ):
        formato_key, valor_mensal_base, valor_mensal_final, valor_tabela_anual, valor_total_anual = self._calcular_valores(
            tipo_licenca,
            formato_pagamento,
            qtd_equipos,
            desconto_percentual,
        )

        linhas = [
            f"Valor de Tabela: {self._dinheiro(valor_tabela_anual)}",
            f"Valor total da anuidade: {self._dinheiro(valor_total_anual)}",
        ]

        if desconto_percentual:
            linhas.append(f"Desconto aplicado: {desconto_percentual * 100:.0f}% sobre o valor da licença.")

        if formato_key == "1":
            linhas.append(
                "Forma de pagamento: Entrada da licença "
                f"{self._dinheiro(valor_mensal_final)} e faltante da licença parcelado em 11 "
                f"(onze) boletos bancários mensais e consecutivos de {self._dinheiro(valor_mensal_final)}."
            )
            linhas.append("Observação: Trata-se de parcelamento do valor anual, não configurando pagamento mensal por serviço.")
        elif formato_key == "2":
            linhas.append(
                "Forma de pagamento: Parcelado o valor integral no cartão em 12x "
                f"de {self._dinheiro(valor_mensal_final)} sem juros."
            )
            linhas.append("Observação: Trata-se de parcelamento do valor anual, não configurando pagamento mensal por serviço.")
        elif formato_key == "3":
            linhas.append(f"Forma de pagamento: Pagamento integral via PIX no valor de {self._dinheiro(valor_total_anual)}.")
            linhas.append("Observação: O pagamento via PIX quita o valor anual da licença.")
        else:
            linhas.append(f"Forma de pagamento: Pagamento mensal recorrente de {self._dinheiro(valor_mensal_final)}.")
            linhas.append("Observação: Condição mensal conforme plano selecionado.")

        return linhas

    def montar_clausula_implantacao(self, tipo_licenca, tipo_implantacao=None, tipo_migracao=None):
        implantacao = self._normalizar_implantacao(tipo_implantacao, tipo_licenca)
        migracao = self._normalizar_migracao(tipo_migracao)

        valor_parcela_migracao_inteligente = (
            self.MIGRACAO_INTELIGENTE_VALOR / self.MIGRACAO_INTELIGENTE_PARCELAS
        )

        if migracao == "isento":
            linhas = [
                "Taxa de Implantação: Isenta.",
                "Migração de Dados: Isenta.",
            ]
        elif tipo_licenca == "1" and migracao == "padrao":
            linhas = [
                "Taxa de Implantação: Isenta.",
                self.IMPLANTACAO_SMART_TEXTO,
            ]
        elif tipo_licenca == "1":
            linhas = [
                "Migração Padrão: inclusa na implantação anual, sendo Dados Cadastrais, tabelas de preço e desenvolvimento clínico vinculado ao CPF do paciente.",
                f"Este backup precisa estar em Excel entregue pelo contratante. Prazo médio de {self.PRAZO_MIGRACAO_PADRAO} após recebimento e validação do arquivo recebido.",
                f"Implantação BASIC: {self.IMPLANTACAO_SMART_TEXTO}",
            ]
        elif migracao == "inteligente":
            linhas = [
                (
                    f"Taxa da Migração: {self._dinheiro(self.MIGRACAO_INTELIGENTE_VALOR)} "
                    f"em {self.MIGRACAO_INTELIGENTE_PARCELAS}x de "
                    f"{self._dinheiro(valor_parcela_migracao_inteligente)} sem juros no cartão."
                ),
                "A APLICATIVO realizará a migração de: Dados Cadastrais, Desenvolvimentos Clínicos, Tabelas de preço, vendas realizadas, manutenções ortodônticas, procedimentos em abertos e concluídos, financeiro com títulos avulsos, contas a receber, recebidos e agenda.",
                "Este backup precisa estar em Excel formato padrão CO entregue pelo contratante, vinculado ao CPF do paciente. Disponibilizamos os templates para preenchimento.",
                f"Prazo: de {self.PRAZO_MIGRACAO_INTELIGENTE} após entrega do Backup e validação da engenharia.",
            ]
        else:
            linhas = [
                "Taxa de Implantação: Isenta.",
                "A APLICATIVO realizará a migração de Dados cadastrais, Tabelas de preços, Histórico de atendimentos (desenvolvimento clínico), desde que vinculados ao CPF do paciente e enviados em planilha Excel no modelo fornecido pela equipe técnica e/ou aprovado da CONTRATADA.",
                f"Este backup precisa estar em Excel entregue pelo contratante. Prazo médio de {self.PRAZO_MIGRACAO_PADRAO} após recebimento e validação do arquivo recebido.",
            ]

        if implantacao == "Clinic":
            linhas.append(self.IMPLANTACAO_CLINIC_TEXTO)

        return linhas

    def aplicar_clausulas_condicionais(
        self,
        doc,
        tipo_licenca,
        formato_pagamento=None,
        qtd_equipos=None,
        tipo_implantacao=None,
        tipo_migracao=None,
        desconto_percentual=0.0,
    ):
        qtd_equipos = qtd_equipos or self.RANGES_EQUIPOS[tipo_licenca][0]
        formato_pagamento = formato_pagamento or "Recorrente"

        self._substituir_secao(
            doc,
            "DO VALOR E DA FORMA DE PAGAMENTO",
            "DA IMPLANTAÇÃO E MIGRAÇÃO DE DADOS",
            self.montar_clausula_financeira(tipo_licenca, formato_pagamento, qtd_equipos, desconto_percentual),
        )
        self._substituir_secao(
            doc,
            "DA IMPLANTAÇÃO E MIGRAÇÃO DE DADOS",
            "DOS SERVIÇOS OPCIONAIS",
            self.montar_clausula_implantacao(tipo_licenca, tipo_implantacao, tipo_migracao),
        )

    def gerar_contrato_pf(self, nome, cpf, tipo_licenca, tipo_implantacao=None, qtd_equipos=None, tipo_migracao=None, observacao=None, formato_pagamento=None, valor_mensal=None, valor_final=None, desconto_percentual=None, valor_entrada=None, num_parcelas=None):
        #"""Gera contrato para pessoa física"""
        # Validação
        cpf_limpo = ValidadorDados.validar_cpf(cpf)
        cpf_formatado = ValidadorDados.formatar_cpf(cpf_limpo)
        
        # Carrega template único
        caminho_template = self.caminho_templates / "Contrato-Aplicativo-Net--MODELO-Placeholder.docx"
        if not caminho_template.exists():
            raise FileNotFoundError(f"Template não encontrado: {caminho_template}")
        
        doc = Document(caminho_template)
        
        # Normaliza valores
        tipo_migracao_norm = self._normalizar_migracao(tipo_migracao)
        
        # Calcula valores padrão se não informados
        if valor_entrada is None:
            valor_entrada = valor_final * 0.5 if valor_final else 0.0
        
        if num_parcelas is None:
            num_parcelas = 12
        
        # Converte número para extenso
        def numero_para_extenso(num):
            numeros_extenso = {
                1: "uma", 2: "duas", 3: "três", 4: "quatro", 5: "cinco",
                6: "seis", 7: "sete", 8: "oito", 9: "nove", 10: "dez",
                11: "onze", 12: "doze", 13: "treze", 14: "catorze", 15: "quinze",
                16: "dezesseis", 17: "dezessete", 18: "dezoito", 19: "dezenove", 20: "vinte",
            }
            return numeros_extenso.get(int(num), str(num))

        parcelas_extenso = numero_para_extenso(num_parcelas)

        # Calcula implantação e migração
        taxa_impl = self.TAXA_IMPLANTACAO.get(self._normalizar_formato_pagamento(formato_pagamento), 490.00)

        valor_migracao = 0.0
        parcelas_migracao = 0
        valor_parcela_migracao = 0.0

        if tipo_migracao_norm == "inteligente":
            valor_migracao = self.MIGRACAO_INTELIGENTE_VALOR
            parcelas_migracao = self.MIGRACAO_INTELIGENTE_PARCELAS
            valor_parcela_migracao = (
                valor_migracao / parcelas_migracao if parcelas_migracao > 0 else 0.0
            )

        # Calcula valor da parcela
        valor_parcela = (valor_final - valor_entrada) / num_parcelas if num_parcelas > 0 else 0.0

        # Prepara substituições
        substituicoes = {
            '[NOMEOURAZAO]': nome,
            '[CONTRATANTE]': nome,
            '[CPF/CNPJ]': cpf_formatado,
            '[CPFCONTRATANTE]': cpf_formatado,
            '[NUMEROPROPOSTA]': datetime.now().strftime('%Y%m%d%H%M%S'),
            '[TIPODELICENÇA]': self.TIPOS_LICENCA[tipo_licenca],
            '[NEQUIPOS]': str(qtd_equipos),
            '[TABELAPRECO]': self._dinheiro(valor_mensal) if valor_mensal else "R$ 0,00",
            '[VALORFINAL]': self._dinheiro(valor_final) if valor_final else "R$ 0,00",
            '[VALORENTRADA]': self._dinheiro(valor_entrada),
            '[PARCELAS]': str(int(num_parcelas)),
            '[PARCELASEXTENSO]': parcelas_extenso,
            '[VALORPARCELA]': self._dinheiro(valor_parcela),
            '[TAXAIMPLANTACAO]': self._dinheiro(taxa_impl),
            '[VALORMIGRACAO]': self._dinheiro(valor_migracao) if valor_migracao > 0 else "R$ 0,00",
            '[PARCELASMIGRACAO]': str(int(parcelas_migracao)) if parcelas_migracao > 0 else "0",
            '[VALORPARCELAMIGRACAO]': self._dinheiro(valor_parcela_migracao) if valor_parcela_migracao > 0 else "R$ 0,00",
            '[VALIDADELICENCA]': (datetime.now() + timedelta(days=365)).strftime('%d/%m/%Y'),
        }

        # Substitui em todo o documento
        self._substituir_em_corpo(doc, substituicoes)
        self._substituir_em_tabelas(doc, substituicoes)

        # Trata cláusula de implantação/migração
        self._aplicar_clausula_implantacao_condicional(doc, tipo_migracao_norm)

        # Salva arquivo
        nome_arquivo = f"{nome}_{cpf_limpo}_{self.TIPOS_LICENCA[tipo_licenca]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        nome_arquivo = self._limpar_nome_arquivo(nome_arquivo)
        caminho_saida = self.caminho_saida / nome_arquivo
        doc.save(caminho_saida)

        return caminho_saida

    def gerar_contrato_pj(self, razao_social, cnpj, tipo_licenca, tipo_implantacao=None, qtd_equipos=None, tipo_migracao=None, observacao=None, formato_pagamento=None, valor_mensal=None, valor_final=None, desconto_percentual=None, valor_entrada=None, num_parcelas=None):
        #"""Gera contrato para pessoa jurídica"""
        # Validação
        cnpj_limpo = ValidadorDados.validar_cnpj(cnpj)
        cnpj_formatado = ValidadorDados.formatar_cnpj(cnpj_limpo)
        
        # Carrega template único
        caminho_template = self.caminho_templates / "Contrato-Aplicativo-Net--MODELO-Placeholder.docx"
        if not caminho_template.exists():
            raise FileNotFoundError(f"Template não encontrado: {caminho_template}")
        
        doc = Document(caminho_template)
        
        # Normaliza valores
        tipo_migracao_norm = self._normalizar_migracao(tipo_migracao)
        
        # Calcula valores padrão se não informados
        if valor_entrada is None:
            valor_entrada = valor_final * 0.5 if valor_final else 0.0
        
        if num_parcelas is None:
            num_parcelas = 12
        
        # Calcula valor da parcela
        saldo_restante = (valor_final or 0.0) - valor_entrada
        valor_parcela = saldo_restante / num_parcelas if num_parcelas > 0 else 0.0
        
        # Converte número para extenso
        def numero_para_extenso(num):
            numeros_extenso = {
                1: "uma", 2: "duas", 3: "três", 4: "quatro", 5: "cinco",
                6: "seis", 7: "sete", 8: "oito", 9: "nove", 10: "dez",
                11: "onze", 12: "doze", 13: "treze", 14: "catorze", 15: "quinze",
                16: "dezesseis", 17: "dezessete", 18: "dezoito", 19: "dezenove", 20: "vinte"
            }
            return numeros_extenso.get(int(num), str(num))
        
        parcelas_extenso = numero_para_extenso(num_parcelas)
        
        # Calcula implantação e migração
        taxa_impl = self.TAXA_IMPLANTACAO.get(self._normalizar_formato_pagamento(formato_pagamento), 490.00)
        
        valor_migracao = 0.0
        parcelas_migracao = 0
        valor_parcela_migracao = 0.0
        
        if tipo_migracao_norm == "inteligente":
            valor_migracao = self.MIGRACAO_INTELIGENTE_VALOR
            parcelas_migracao = self.MIGRACAO_INTELIGENTE_PARCELAS
            valor_parcela_migracao = valor_migracao / parcelas_migracao if parcelas_migracao > 0 else 0.0
        
        # Prepara substituições
        substituicoes = {
            '[NOMEOURAZAO]': razao_social,
            '[CONTRATANTE]': razao_social,
            '[CPF/CNPJ]': cnpj_formatado,
            '[CPFCONTRATANTE]': cnpj_formatado,
            '[NUMEROPROPOSTA]': datetime.now().strftime('%Y%m%d%H%M%S'),
            '[TIPODELICENÇA]': self.TIPOS_LICENCA[tipo_licenca],
            '[NEQUIPOS]': str(qtd_equipos),
            '[TABELAPRECO]': self._dinheiro(valor_mensal) if valor_mensal else "R$ 0,00",
            '[VALORFINAL]': self._dinheiro(valor_final) if valor_final else "R$ 0,00",
            '[VALORENTRADA]': self._dinheiro(valor_entrada),
            '[PARCELAS]': str(int(num_parcelas)),
            '[PARCELASEXTENSO]': parcelas_extenso,
            '[VALORPARCELA]': self._dinheiro(valor_parcela),
            '[TAXAIMPLANTACAO]': self._dinheiro(taxa_impl),
            '[VALORMIGRACAO]': self._dinheiro(valor_migracao) if valor_migracao > 0 else "R$ 0,00",
            '[PARCELASMIGRACAO]': str(int(parcelas_migracao)) if parcelas_migracao > 0 else "0",
            '[VALORPARCELAMIGRACAO]': self._dinheiro(valor_parcela_migracao) if valor_parcela_migracao > 0 else "R$ 0,00",
            '[VALIDADELICENCA]': (datetime.now() + timedelta(days=365)).strftime('%d/%m/%Y'),
        }
        
        # Substitui em todo o documento
        self._substituir_em_corpo(doc, substituicoes)
        self._substituir_em_tabelas(doc, substituicoes)
        
        # Trata cláusula de implantação/migração
        self._aplicar_clausula_implantacao_condicional(doc, tipo_migracao_norm)
        
        # Salva arquivo
        nome_arquivo = f"{razao_social}_{cnpj_limpo}_{self.TIPOS_LICENCA[tipo_licenca]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        nome_arquivo = self._limpar_nome_arquivo(nome_arquivo)
        caminho_saida = self.caminho_saida / nome_arquivo
        doc.save(caminho_saida)
        
        return caminho_saida

    def _aplicar_clausula_implantacao_condicional(self, doc, tipo_migracao):
        #"""Remove a cláusula de implantação que não foi escolhida"""
        # Localiza os parágrafos das duas opções
        opcao1_encontrada = False
        opcao2_encontrada = False
        parafos_opcao1 = []
        parafos_opcao2 = []
        em_opcao1 = False
        em_opcao2 = False
        
        for i, parafo in enumerate(doc.paragraphs):
            texto = parafo.text.strip()
            
            # Marca início da Opção 1 (Padrão)
            if "Implantação Padrão" in texto or "10 a 15 dias" in texto:
                em_opcao1 = True
                opcao1_encontrada = True
            
            # Marca início da Opção 2 (Completa)
            if "Opção 02" in texto or "Migração Completa" in texto:
                em_opcao2 = True
                opcao2_encontrada = True
                em_opcao1 = False
            
            # Coleta parágrafos por opção
            if em_opcao1 and not em_opcao2:
                parafos_opcao1.append(parafo)
            elif em_opcao2:
                parafos_opcao2.append(parafo)
        
        # Remove a opção não selecionada
        if tipo_migracao == "inteligente":
            # Mantém Opção 2, remove Opção 1
            for parafo in parafos_opcao1:
                self._remover_paragrafo(parafo)
        else:
            # Mantém Opção 1, remove Opção 2
            for parafo in parafos_opcao2:
                self._remover_paragrafo(parafo)

    def _limpar_nome_arquivo(self, nome_arquivo):
        return re.sub(r'[<>:"/\\|?*]', "_", nome_arquivo)

    def listar_tipos_licenca(self):
        print("\n--- TIPOS DE LICENÇA ---")
        for chave, nome in self.TIPOS_LICENCA.items():
            print(f"{chave} - {nome}")

    def _normalizar_migracao(self, tipo_migracao):
    #"""Normaliza o tipo de migração"""
        if tipo_migracao is None:
            return "isento"
        
        tipo_lower = str(tipo_migracao).lower().strip()
        
        if "inteligente" in tipo_lower or "smart" in tipo_lower or "completa" in tipo_lower:
            return "inteligente"
        elif "padrão" in tipo_lower or "padrao" in tipo_lower or "basico" in tipo_lower:
            return "padrao"
        else:
            return "isento"


def main():
    gerador = Gerador()
    print("\n=== GERADOR DE CONTRATOS ===\n")
    tipo_pessoa = input("Tipo de cliente (1=Pessoa Física, 2=Pessoa Jurídica): ").strip()

    if tipo_pessoa == "1":
        nome = input("Nome completo: ").strip()
        cpf = input("CPF: ").strip()
        gerador.listar_tipos_licenca()
        tipo_licenca = input("\nEscolha o tipo de licença (1-5): ").strip()
        caminho = gerador.gerar_contrato_pf(nome, cpf, tipo_licenca)
        print(f"\nContrato gerado com sucesso: {caminho}")
    elif tipo_pessoa == "2":
        razao_social = input("Razão Social: ").strip()
        cnpj = input("CNPJ: ").strip()
        gerador.listar_tipos_licenca()
        tipo_licenca = input("\nEscolha o tipo de licença (1-5): ").strip()
        caminho = gerador.gerar_contrato_pj(razao_social, cnpj, tipo_licenca)
        print(f"\nContrato gerado com sucesso: {caminho}")
    else:
        print("Opção inválida.")


if __name__ == "__main__":
    main()
