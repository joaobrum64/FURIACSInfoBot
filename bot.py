import os
import logging
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime


#Logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger()


#.env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_API_KEY")
PANDASCORE_API_KEY = os.getenv("PANDASCORE_API_KEY")


# fetch api
def fetch_data(endpoint, params=None):
    try:
        headers = {"Authorization": f"Bearer {PANDASCORE_API_KEY}"}
        response = requests.get(endpoint, params=params, headers=headers)
        logger.info(f"URL: {response.url}")
        logger.info(f"Status: {response.status_code}")
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Fetch API error: {str(e)}")
        return None


#/start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Olá! Sou o FURIACSInfo, bot de informações da FURIA Esports no CS! Digite um dos comandos abaixo para obter informações.\n\n"
        "Comandos:\n\n"
        "/lineup -> Atual lineup da FURIA\n"
        "/calendario -> Próximos campeonatos da FURIA\n"
        "/jogador [nome] -> Informações sobre os jogadores da FURIA\n"
        "/historia -> História resumida da FURIA no CS\n"
        "/bot -> Informações do bot"
    )


#/lineup
async def lineup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    team_id = "124530"
    teams_endpoint = "https://api.pandascore.co/csgo/teams"
    params = {"filter[id]": team_id}
    lineup_data = fetch_data(teams_endpoint, params=params)
    if lineup_data and len(lineup_data) > 0:
        team = lineup_data[0]
        all_players = team.get("players", [])
        
        #Correção
        main_lineup_names = ["FalleN", "YEKINDAR", "yuurih", "KSCERATO", "molodoy"]
        #

        main_players = [player for player in all_players if player["name"] in main_lineup_names]
        players = "\n".join(player["name"] for player in main_players)
        await update.message.reply_text(f"Lineup atual da FURIA:\n{players}")
    else:
        await update.message.reply_text("Não foi possível obter a lineup no momento.")


#/calendario
async def calendario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        matches_endpoint = "https://api.pandascore.co/csgo/matches/upcoming"
        params = {"filter[opponent_id]": "124530"}
        matches_data = fetch_data(matches_endpoint, params=params)

        #Correção
        manual_events = [
            {"date": "2025-05-10", "tournament": "PGL Astana 2025"},
            {"date": "2025-05-19", "tournament": "IEM Dallas 2025"},
            {"date": "2025-06-07", "tournament": "Blast.tv Austin Major 2025 Stage 2"}
        ]
        #
  
        upcoming_matches = []
        if matches_data and len(matches_data) > 0:
            for match in matches_data:
                tournament_name = match.get("tournament", {}).get("name", "N/A")
                date = match.get("begin_at", "N/A")[:10] 
                upcoming_matches.append({"date": date, "tournament": tournament_name})


        upcoming_matches.extend(manual_events)
        upcoming_matches = sorted(upcoming_matches, key=lambda x: x["date"])

        formatted_matches = [
            f"{'/'.join(reversed(event['date'].split('-')))} {event['tournament']}" for event in upcoming_matches
        ]

        if len(formatted_matches) > 0:
            response = "Próximos jogos da FURIA:\n" + "\n".join(formatted_matches)
            await update.message.reply_text(response)
        else:
            await update.message.reply_text("Não foram encontrados próximos jogos para a FURIA.")
    except Exception as e:
        logger.error(f"Erro ao buscar próximos jogos: {str(e)}")
        await update.message.reply_text("Ocorreu um erro ao buscar os próximos jogos. Por favor, tente novamente mais tarde.")


#/jogador
async def jogador(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        #Correção
        manual_birthdates = {
            "FalleN": "1991-05-30",
            "YEKINDAR": "1999-10-04",
            "yuurih": "1999-12-22",
            "KSCERATO": "1999-09-12",
            "molodoy": "2005-01-10"
        }
        #
        
        user_message = update.message.text.strip()
        command_parts = user_message.split(" ", 1)
        
        if len(command_parts) < 2:
            await update.message.reply_text("Por favor, use o comando no formato: /jogador [nome].")
            return
        
        player_name = command_parts[1].strip().lower()

        valid_player_key = next((key for key in manual_birthdates if key.lower() == player_name), None)
        if not valid_player_key:
            await update.message.reply_text(
                "Jogador não encontrado na atual lineup da FURIA. Por favor, informe um dos seguintes nomes:\n" +
                ", ".join(manual_birthdates.keys())
            )
            return

        player_endpoint = "https://api.pandascore.co/csgo/players"
        params = {"search[name]": valid_player_key}
        player_data = fetch_data(player_endpoint, params=params)

        if player_data and len(player_data) > 0:
            player_info = player_data[0]
            full_name = f"{player_info.get('first_name', 'Desconhecido')} \"{player_info.get('name', 'Desconhecido')}\" {player_info.get('last_name', 'Desconhecido')}"
            nationality = player_info.get("nationality", "Desconhecida")
            current_team = player_info.get("current_team", {}).get("name", "Desconhecido")
            
            # Correção
            birthdate = manual_birthdates[valid_player_key]
            birthdate_formatted = "/".join(reversed(birthdate.split("-")))
            #
            
            birth_year, birth_month, birth_day = map(int, birthdate.split("-"))
            today = datetime.now()
            age = today.year - birth_year - ((today.month, today.day) < (birth_month, birth_day))

            response = (
                f"Informações sobre {valid_player_key}:\n"
                f"Nome: {full_name}\n"
                f"Idade: {age} anos ({birthdate_formatted})\n"
                f"Nacionalidade: {nationality}\n"
                f"Time atual: {current_team}"
            )
            await update.message.reply_text(response)
        else:
            await update.message.reply_text(f"Não foi possível encontrar informações sobre o jogador {valid_player_key} no momento.")
    except Exception as e:
        logger.error(f"Erro ao buscar informações do jogador: {str(e)}")
        await update.message.reply_text("Ocorreu um erro ao buscar informações sobre o jogador. Por favor, tente novamente mais tarde.")


#/historia
async def historia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sobre_text = """
A FURIA Esports teve inicio na sua fundação em 8 de agosto de 2017, em Uberlândia, Minas Gerais, pelos empresários Jaime Pádua, André Akkari e Cristian Guedes.

Inicialmente, o foco foi no cenário de CSGO, onde rapidamente ganhou notoriedade. Em 2019, a participação no IEM Katowice Major marcou a estreia em torneios de grande porte. Apesar de não avançar nas fases finais, a evolução era constante e, no mesmo ano, conquistou o segundo lugar na 7ª temporada do Esports Championship Series (ECS). Em 2020, a FURIA venceu ESL Pro League Season 12 da América do Norte, consolidando sua posição e reconhecimento como melhor organização de esports no Brasil em 2020 e 2021, pelo Prêmio eSports Brasil e como a quinta maior organização de esports do mundo em 2022 pelo portal Nerd Street.

Com o crescimento contínuo, a FURIA se estabeleceu em escritórios por São Paulo, Estados Unidos e Malta, para facilitar a participação em torneios internacionais, além de expandir ramos para outros jogos (como League of Legends, Valorant, Rainbow Six Siege, Apex Legends e Rocket League) e esportes como futebol 7 (participando da Kings World Cup)e no automobilismo por meio da entrada na Porsche Cup Brasil.
    """
    await update.message.reply_text(sobre_text)


#/bot
async def bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_text = """
Bot feito por joaobrum64:

https://github.com/joaobrum64

https://www.linkedin.com/in/jpbl

Recursos utilizados:

Python (telegram-bot, dotenv, requests)

PandaScore API

BotFather (telegram)
    """
    await update.message.reply_text(bot_text)    


#run
if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("lineup", lineup))
    application.add_handler(CommandHandler("calendario", calendario))
    application.add_handler(CommandHandler("jogador", jogador))
    application.add_handler(CommandHandler("historia", historia))
    application.add_handler(CommandHandler("bot", bot))
    
    application.run_polling()