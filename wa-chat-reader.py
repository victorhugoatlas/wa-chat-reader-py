import customtkinter as ctk
from tkinter import filedialog, messagebox
import re
import os
import base64
import mimetypes
import urllib.parse
import threading
from concurrent.futures import ThreadPoolExecutor

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class WAReader(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("WA Chat Reader by VH")
        self.geometry("540x480")
        self.pasta_selecionada = ""

        self.label_titulo = ctk.CTkLabel(self, text="WA Chat Reader by VH", font=("Segoe UI", 22, "bold"))
        self.label_titulo.pack(pady=20)

        self.btn_procurar = ctk.CTkButton(self, text="📁 Selecionar Pasta do Chat", command=self.selecionar_pasta, font=("Segoe UI", 13, "bold"))
        self.btn_procurar.pack(pady=10)

        self.label_status = ctk.CTkLabel(self, text="Nenhuma pasta selecionada", font=("Segoe UI", 12))
        self.label_status.pack(pady=5)

        self.progressbar = ctk.CTkProgressBar(self, width=420)
        self.progressbar.pack(pady=15)
        self.progressbar.set(0)

        self.label_progresso = ctk.CTkLabel(self, text="", font=("Segoe UI", 11, "italic"), text_color="#aaaaaa")
        self.label_progresso.pack(pady=2)

        self.frame_botoes = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_botoes.pack(pady=15)

        self.btn_rapido = ctk.CTkButton(
            self.frame_botoes, text="⚡ Modo Rápido (Links Local)", command=lambda: self.iniciar_processamento_thread(modo="relativo"),
            state="disabled", fg_color="#3b82f6", hover_color="#1d4ed8", font=("Segoe UI", 12, "bold"), width=200
        )
        self.btn_rapido.grid(row=0, column=0, padx=8, pady=5)

        self.btn_portatil = ctk.CTkButton(
            self.frame_botoes, text="📦 Modo Portátil (Embed Base64)", command=lambda: self.iniciar_processamento_thread(modo="base64"),
            state="disabled", fg_color="#25D366", hover_color="#128C7E", text_color="black", font=("Segoe UI", 12, "bold"), width=200
        )
        self.btn_portatil.grid(row=0, column=1, padx=8, pady=5)

    def selecionar_pasta(self):
        self.pasta_selecionada = filedialog.askdirectory()
        if self.pasta_selecionada:
            self.label_status.configure(text=f"Pasta: {os.path.basename(self.pasta_selecionada)}")
            self.btn_rapido.configure(state="normal")
            self.btn_portatil.configure(state="normal")
            self.progressbar.set(0)
            self.label_progresso.configure(text="")

    def converter_arquivo_base64(self, caminho_arq):
        """Converte arquivos locais em Base64 Data-URI para embutir no HTML."""
        try:
            mime_type, _ = mimetypes.guess_type(caminho_arq)
            ext = os.path.splitext(caminho_arq)[1].lower()
            
            if ext == '.opus':
                mime_type = 'audio/ogg'
            elif ext == '.m4a':
                mime_type = 'audio/mp4'
            elif ext == '.webp':
                mime_type = 'image/webp'
            elif ext == '.mov':
                mime_type = 'video/quicktime'
            elif not mime_type:
                mime_type = 'application/octet-stream'

            with open(caminho_arq, "rb") as f:
                encoded_string = base64.b64encode(f.read()).decode('utf-8')
            return caminho_arq, f"data:{mime_type};base64,{encoded_string}"
        except Exception as e:
            print(f"Erro ao converter {caminho_arq}: {e}")
            return caminho_arq, ""

    def iniciar_processamento_thread(self, modo):
        self.btn_rapido.configure(state="disabled")
        self.btn_portatil.configure(state="disabled")
        self.btn_procurar.configure(state="disabled")
        threading.Thread(target=self.processar, args=(modo,), daemon=True).start()

    def processar(self, modo):
        try:
            caminho_pasta = self.pasta_selecionada
            arquivo_txt = os.path.join(caminho_pasta, "_chat.txt")

            if not os.path.exists(arquivo_txt):
                self.after(0, lambda: messagebox.showerror("Erro", "Arquivo _chat.txt não encontrado nesta pasta!"))
                self.restaurar_botoes()
                return

            nome_destinatario = os.path.basename(caminho_pasta).lower().strip()
            pasta_pai = os.path.dirname(caminho_pasta)
            sufixo = "Portatil" if modo == "base64" else "Rapido"
            nome_html = f"Leitura_{os.path.basename(caminho_pasta)}_{sufixo}.html"
            caminho_saida = os.path.join(pasta_pai, nome_html)

            padrao = re.compile(r'\[(\d{2}/\d{2}/\d{4}),\s(\d{2}:\d{2}:\d{2})\]\s(.*?):\s(.*)')
            cache_base64 = {}

            if modo == "base64":
                self.after(0, self.atualizar_progresso, 0.05, "Mapeando mídias para conversão Base64...")
                arquivos_para_converter = set()

                with open(arquivo_txt, 'r', encoding='utf-8') as f:
                    for linha in f:
                        linha_limpa = linha.replace('\u200e', '').replace('\u200f', '').strip()
                        match = padrao.match(linha_limpa)
                        if match:
                            conteudo = match.group(4)
                            if "<anexado:" in conteudo:
                                arq_match = re.search(r'<anexado:\s*(.*?)>', conteudo)
                                if arq_match:
                                    nome_arq = arq_match.group(1).strip()
                                    caminho_arq = os.path.join(caminho_pasta, nome_arq)
                                    if os.path.exists(caminho_arq):
                                        arquivos_para_converter.add(caminho_arq)

                total_midias = len(arquivos_para_converter)

                if total_midias > 0:
                    max_workers = min(16, (os.cpu_count() or 4) * 2)
                    concluidos = 0

                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        futures = [executor.submit(self.converter_arquivo_base64, arq) for arq in arquivos_para_converter]
                        for future in futures:
                            caminho_arq, data_uri = future.result()
                            cache_base64[caminho_arq] = data_uri
                            concluidos += 1
                            pct = 0.05 + (concluidos / total_midias) * 0.80
                            self.after(0, self.atualizar_progresso, pct, f"Embutindo mídias ({concluidos}/{total_midias})...")
            else:
                self.after(0, self.atualizar_progresso, 0.20, "Montando estrutura HTML (Modo Rápido)...")

            self.after(0, self.atualizar_progresso, 0.90, "Gravando arquivo HTML no disco...")

            html_header = """<html><head><meta charset="utf-8"><style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0b141a; color: #e9edef; padding: 20px; }
                .chat { max-width: 850px; margin: auto; display: flex; flex-direction: column; }
                .msg { padding: 8px 12px; margin: 4px; border-radius: 8px; max-width: 75%; box-shadow: 0 1px 1px rgba(0,0,0,0.3); font-size: 14px; line-height: 19px; }
                .recebida { background: #202c33; align-self: flex-start; border-top-left-radius: 0; }
                .enviada { background: #005c4b; align-self: flex-end; border-top-right-radius: 0; }
                .nome { font-weight: bold; font-size: 0.8em; color: #53bdeb; margin-bottom: 3px; display: block; }
                .meta { font-size: 0.68em; color: #8696a0; display: block; text-align: right; margin-top: 4px; }
                img, video { max-width: 100%; max-height: 380px; border-radius: 6px; margin-top: 5px; display: block; object-fit: contain; }
                img.sticker { width: 130px; height: 130px; background: transparent; box-shadow: none; }
                audio { width: 280px; margin-top: 6px; }
                .doc-box { display: flex; align-items: center; background: rgba(0,0,0,0.2); padding: 8px 12px; border-radius: 6px; margin-top: 6px; text-decoration: none; color: #e9edef; border: 1px solid #3b4a54; font-size: 0.9em; }
            </style></head><body><div class="chat">\n"""

            with open(caminho_saida, "w", encoding="utf-8") as f_out:
                f_out.write(html_header)

                with open(arquivo_txt, 'r', encoding='utf-8') as f_in:
                    for linha in f_in:
                        linha_limpa = linha.replace('\u200e', '').replace('\u200f', '').strip()
                        match = padrao.match(linha_limpa)
                        
                        if match:
                            data, hora, nome, conteudo = match.groups()
                            nome_limpo = nome.strip()

                            if nome_limpo.lower() in nome_destinatario or nome_destinatario in nome_limpo.lower():
                                classe = "recebida"
                            else:
                                classe = "enviada"

                            midia_tag = ""
                            
                            if "<anexado:" in conteudo:
                                arq_match = re.search(r'<anexado:\s*(.*?)>', conteudo)
                                if arq_match:
                                    nome_arq = arq_match.group(1).strip()
                                    caminho_arq = os.path.join(caminho_pasta, nome_arq)
                                    ext = os.path.splitext(nome_arq)[1].lower()

                                    if modo == "base64":
                                        src_midia = cache_base64.get(caminho_arq, "")
                                    else:
                                        if os.path.exists(caminho_arq):
                                            src_midia = "file:///" + urllib.parse.quote(caminho_arq.replace("\\", "/"))
                                        else:
                                            src_midia = ""

                                    if src_midia:
                                        if ext in ['.jpg', '.jpeg', '.png']:
                                            midia_tag = f'<img src="{src_midia}">'
                                        elif ext == '.webp':
                                            midia_tag = f'<img src="{src_midia}" class="sticker">'
                                        elif ext in ['.mp4', '.mov']:
                                            midia_tag = f'<video controls src="{src_midia}"></video>'
                                        elif ext in ['.opus', '.m4a', '.mp3', '.ogg']:
                                            midia_tag = f'<audio controls src="{src_midia}"></audio>'
                                        else:
                                            midia_tag = f'<a href="{src_midia}" target="_blank" class="doc-box">📄 Arquivo {ext.upper()}: {nome_arq}</a>'

                            texto = re.sub(r'<anexado:.*?>', '', conteudo).strip()
                            texto_p = f"<p style='margin:4px 0;'>{texto}</p>" if texto else ""
                            
                            f_out.write(f'<div class="msg {classe}"><span class="nome">{nome_limpo}</span>{midia_tag}{texto_p}<span class="meta">{data} {hora}</span></div>\n')

                f_out.write("</div></body></html>")

            self.after(0, lambda: self.finalizar_sucesso(caminho_saida))

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erro Crítico", f"Ocorreu um erro: {e}"))
            self.restaurar_botoes()

    def atualizar_progresso(self, valor, texto):
        self.progressbar.set(valor)
        self.label_progresso.configure(text=texto)

    def finalizar_sucesso(self, caminho_saida):
        self.progressbar.set(1.0)
        self.label_progresso.configure(text="Concluído com sucesso!")
        messagebox.showinfo("Sucesso", f"Arquivo HTML gerado com sucesso!\nSalvo em: {caminho_saida}")
        os.startfile(os.path.dirname(caminho_saida))
        self.restaurar_botoes()

    def restaurar_botoes(self):
        self.btn_rapido.configure(state="normal")
        self.btn_portatil.configure(state="normal")
        self.btn_procurar.configure(state="normal")

if __name__ == "__main__":
    app = WAReader()
    app.mainloop()