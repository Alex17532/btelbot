import discord
from discord.ext import commands,tasks
import asyncio,csv,io,requests
from typing import List,Dict,Optional
import re
from collections import defaultdict,Counter
from datetime import datetime
import statistics
import os
intents=discord.Intents.default()
intents.message_content=True
bot=commands.Bot(command_prefix='!',intents=intents,help_command=None)
SHEET_URL='https://docs.google.com/spreadsheets/d/19pi4JoomyimkKCFAzDVLYHjai16MiPBM-4y_NgucSKo/export?format=csv&gid=1821177716'
class BlockTanksData:
	def __init__(self):self.matches=[];self.players=set();self.player_stats={};self.last_updated=None
	async def load_data(self):
		'Load data from Google Sheets and parse player statistics'
		try:
			response=requests.get(SHEET_URL);response.raise_for_status();csv_reader=csv.reader(io.StringIO(response.text));rows=list(csv_reader);self.matches=[];self.players=set();self.player_stats={};current_player=None
			for(i,row)in enumerate(rows):
				if len(row)>1:
					if row[0]=='Player:'and len(row)>1 and row[1].strip():current_player=row[1].strip();self.players.add(current_player);self.player_stats[current_player]=self.init_player_stats();continue
					if current_player and len(row)>2:self.parse_player_row(current_player,row)
			self.generate_matches_from_stats();self.last_updated=datetime.now();print(f"Loaded data for {len(self.players)} players with {len(self.matches)} synthetic matches");return True
		except Exception as e:print(f"Error loading data: {e}");return False
	def init_player_stats(self):'Initialize empty player statistics';return{'wins':0,'losses':0,'draws':0,'kills':0,'deaths':0,'matches_played':0,'points':0,'kdr':0,'winrate':0,'regions':{},'maps':{},'opponents_beaten':Counter(),'opponents_lost_to':Counter()}
	def parse_player_row(self,player,row):
		'Parse a row of player data'
		try:
			if len(row)<3:return
			label=row[0].strip()if row[0]else'';value=row[1].strip()if len(row)>1 and row[1]else'';stats=self.player_stats[player]
			if'Total Wins'in label:stats['wins']=self.safe_int(value)
			elif'Total Losses'in label:stats['losses']=self.safe_int(value)
			elif'Total Draws'in label:stats['draws']=self.safe_int(value)
			elif'Total Kills'in label:stats['kills']=self.safe_int(value)
			elif'Total Deaths'in label:stats['deaths']=self.safe_int(value)
			elif'Total Matches Played'in label:stats['matches_played']=self.safe_int(value)
			elif'Current Points'in label:stats['points']=self.safe_float(value)
			elif'Average K/D Ratio'in label:stats['kdr']=self.safe_float(value)
			if len(row)>8 and row[2]and row[2].strip()in['EU','USA','AS','NA']:
				region=row[2].strip()
				if region not in stats['regions']:stats['regions'][region]={'wins':self.safe_int(row[3])if len(row)>3 else 0,'losses':self.safe_int(row[4])if len(row)>4 else 0,'draws':self.safe_int(row[5])if len(row)>5 else 0,'kills':self.safe_int(row[6])if len(row)>6 else 0,'deaths':self.safe_int(row[7])if len(row)>7 else 0,'matches':self.safe_int(row[8])if len(row)>8 else 0}
			if len(row)>8 and row[2]and row[2].strip()in['Terror','Tiny Town','Blitz','Arena','Mini Nukes','Halls 2.0']:
				map_name=row[2].strip()
				if map_name not in stats['maps']:stats['maps'][map_name]={'wins':self.safe_int(row[3])if len(row)>3 else 0,'losses':self.safe_int(row[4])if len(row)>4 else 0,'draws':self.safe_int(row[5])if len(row)>5 else 0,'kills':self.safe_int(row[6])if len(row)>6 else 0,'deaths':self.safe_int(row[7])if len(row)>7 else 0,'matches':self.safe_int(row[8])if len(row)>8 else 0}
		except Exception as e:print(f"Error parsing row for {player}: {e}")
	def generate_matches_from_stats(self):
		'Generate synthetic match data from player statistics';match_id=0
		for(player,stats)in self.player_stats.items():
			for(region,region_stats)in stats['regions'].items():
				for _ in range(region_stats['matches']):match_id+=1;match={'id':match_id,'winner':player,'loser':'Unknown Opponent','winner_kills':region_stats['kills']//max(region_stats['matches'],1),'loser_kills':region_stats['deaths']//max(region_stats['matches'],1),'winner_points':stats['points']//max(stats['matches_played'],1),'loser_points':0,'map':list(stats['maps'].keys())[0]if stats['maps']else'Unknown','region':region,'outcome':'Win'if region_stats['wins']>0 else'Loss','date':datetime.now().strftime('%Y-%m-%d'),'time':'00:00:00','tournament':'','season':'Season 1'};self.matches.append(match)
	def safe_int(self,value):
		try:return int(float(value))if value else 0
		except:return 0
	def safe_float(self,value):
		try:return float(value)if value else .0
		except:return .0
game_data=BlockTanksData()
@bot.event
async def on_ready():print(f"{bot.user} has connected to Discord!");await game_data.load_data();auto_refresh_data.start();print('Data loaded successfully!')
@tasks.loop(minutes=5)
async def auto_refresh_data():
	success=await game_data.load_data()
	if success:print(f"✅ Auto-refreshed at {datetime.now()}")
	else:print('❌ Auto-refresh failed')
@bot.command(name='refresh')
async def refresh_data(ctx):
	'Refresh data from the spreadsheet';await ctx.send('🔄 Refreshing data from spreadsheet...');success=await game_data.load_data()
	if success:await ctx.send(f"✅ Data refreshed! Loaded {len(game_data.players)} players and {len(game_data.matches)} matches.\nLast updated: {game_data.last_updated.strftime("%Y-%m-%d %H:%M:%S")}")
	else:await ctx.send('❌ Failed to refresh data. Please try again later.')
@bot.command(name='player')
async def player_stats(ctx,*,player_name=None):
	'Get comprehensive stats for a specific player'
	if not player_name:await ctx.send('Please provide a player name: `!player PlayerName`');return
	found_player=None
	for p in game_data.players:
		if p.lower()==player_name.lower():found_player=p;break
	if not found_player:similar=[p for p in game_data.players if player_name.lower()in p.lower()];suggestion_text=f"\nDid you mean: {", ".join(similar[:5])}"if similar else'';await ctx.send(f"Player '{player_name}' not found.{suggestion_text}");return
	stats=game_data.player_stats[found_player];total_games=stats['wins']+stats['losses']+stats['draws'];win_rate=stats['wins']/max(total_games,1)*100;kdr=stats['kills']/max(stats['deaths'],1);embed=discord.Embed(title=f"📊 Detailed Stats for {found_player}",color=65280);embed.add_field(name='🏆 Overall Record',value=f"**{stats["wins"]}W - {stats["losses"]}L - {stats["draws"]}D**\nWin Rate: **{win_rate:.1f}%**\nTotal Games: **{total_games}**",inline=True);embed.add_field(name='⚔️ Combat Performance',value=f"**{stats["kills"]}** total kills\n**{stats["deaths"]}** total deaths\n**{kdr:.2f}** K/D ratio",inline=True);embed.add_field(name='📈 Points',value=f"**{stats["points"]:.1f}** total points\n**{stats["points"]/max(total_games,1):.1f}** avg points/game",inline=True)
	if stats['regions']:
		region_text=''
		for(region,region_stats)in stats['regions'].items():region_games=region_stats['matches'];region_wr=region_stats['wins']/max(region_games,1)*100;region_kdr=region_stats['kills']/max(region_stats['deaths'],1);region_text+=f"**{region}**: {region_stats["wins"]}W-{region_stats["losses"]}L-{region_stats["draws"]}D ({region_wr:.1f}% WR, {region_kdr:.2f} K/D)\n"
		embed.add_field(name='🌍 Regional Performance',value=region_text,inline=False)
	if stats['maps']:
		map_text=''
		for(map_name,map_stats)in stats['maps'].items():map_games=map_stats['matches'];map_wr=map_stats['wins']/max(map_games,1)*100;map_kdr=map_stats['kills']/max(map_stats['deaths'],1);map_text+=f"**{map_name}**: {map_stats["wins"]}W-{map_stats["losses"]}L-{map_stats["draws"]}D ({map_wr:.1f}% WR, {map_kdr:.2f} K/D)\n"
		embed.add_field(name='🗺️ Map Performance',value=map_text,inline=False)
	await ctx.send(embed=embed)
@bot.command(name='leaderboard',aliases=['lb','top'])
async def leaderboard(ctx,stat='points'):
	'Show leaderboard by various stats';valid_stats=['wins','points','kdr','kills','winrate','matches']
	if stat.lower()not in valid_stats:await ctx.send(f"Invalid stat. Choose from: {", ".join(valid_stats)}");return
	leaderboard_data=[]
	for(player,stats)in game_data.player_stats.items():
		total_games=stats['wins']+stats['losses']+stats['draws']
		if total_games>0:win_rate=stats['wins']/total_games*100;kdr=stats['kills']/max(stats['deaths'],1);player_data={'player':player,'wins':stats['wins'],'points':stats['points'],'kdr':kdr,'kills':stats['kills'],'winrate':win_rate,'matches':total_games};leaderboard_data.append(player_data)
	leaderboard_data.sort(key=lambda x:x[stat.lower()],reverse=True);stat_names={'wins':'🏆 Wins Leaderboard','points':'📈 Points Leaderboard','kdr':'⚔️ K/D Ratio Leaderboard','kills':'💀 Kills Leaderboard','winrate':'📊 Win Rate Leaderboard','matches':'🎮 Matches Played Leaderboard'};embed=discord.Embed(title=stat_names[stat.lower()],color=16766720);leaderboard_text=''
	for(i,data)in enumerate(leaderboard_data[:10],1):
		medal='🥇'if i==1 else'🥈'if i==2 else'🥉'if i==3 else f"{i}."
		if stat.lower()in['points']:value=f"{data[stat.lower()]:.1f}"
		elif stat.lower()in['kdr','winrate']:
			value=f"{data[stat.lower()]:.2f}"
			if stat.lower()=='winrate':value+='%'
		else:value=str(int(data[stat.lower()]))
		leaderboard_text+=f"{medal} **{data["player"]}** - {value} ({data["matches"]} games)\n"
	embed.description=leaderboard_text;await ctx.send(embed=embed)
@bot.command(name='stats')
async def global_stats(ctx):
	'Show overall league statistics'
	if not game_data.players:await ctx.send('No data available. Use `!refresh` to load data.');return
	total_players=len(game_data.players);total_matches=len(game_data.matches);total_kills=sum(stats['kills']for stats in game_data.player_stats.values());total_points=sum(stats['points']for stats in game_data.player_stats.values());most_active=max(game_data.player_stats.items(),key=lambda x:x[1]['matches_played']);embed=discord.Embed(title='📊 BlockTanks League - Global Statistics',color=65535);embed.add_field(name='🎮 Overall Activity',value=f"**{total_players}** registered players\n**{total_matches}** total matches\n**{total_kills:,}** total eliminations\n**{total_points:,.1f}** total points awarded",inline=True);embed.add_field(name='👑 Most Active Player',value=f"**{most_active[0]}**\n{most_active[1]["matches_played"]} games played",inline=True)
	if game_data.last_updated:embed.add_field(name='🔄 Data Status',value=f"Last updated:\n{game_data.last_updated.strftime("%Y-%m-%d %H:%M:%S")}",inline=True)
	await ctx.send(embed=embed)
@bot.command(name='help')
async def help_command(ctx):'Show all available commands';embed=discord.Embed(title='🤖 BlockTanks League Bot - Command Guide',color=7506394);commands_text='\n**Player Commands:**\n`!player <name>` - Comprehensive player statistics\n`!leaderboard [stat]` - Show leaderboards (wins/points/kdr/kills/winrate/matches)\n\n**System Commands:**\n`!refresh` - Refresh data from spreadsheet\n`!stats` - Show global league statistics\n`!help` - Show this help message\n\n**Available Stats for Leaderboard:**\n• `wins` - Total wins\n• `points` - Total points\n• `kdr` - Kill/Death ratio\n• `kills` - Total kills\n• `winrate` - Win percentage\n• `matches` - Total matches played\n\n**Examples:**\n`!player NYS Lask` - Get detailed player stats\n`!leaderboard points` - Points leaderboard\n`!leaderboard winrate` - Win rate leaderboard\n    ';embed.description=commands_text;await ctx.send(embed=embed)
if __name__=='__main__':bot.run(os.getenv('DISCORD_TOKEN'))
