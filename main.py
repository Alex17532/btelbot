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
SHEET_URL='https://docs.google.com/spreadsheets/d/1r-5WoC6DcaCk9zJAz2Ct9b531AgoOIpvc98xm8oGg4w/export?format=csv&gid=741413211'
class BlockTanksData:
	def __init__(self):self.matches=[];self.players=set();self.last_updated=None
	async def load_data(self):
		'Load data from Google Sheets with enhanced processing'
		try:
			response=requests.get(SHEET_URL);response.raise_for_status();csv_reader=csv.DictReader(io.StringIO(response.text));self.matches=[];self.players=set()
			for row in csv_reader:
				if row.get('Winner/P1')and row.get('Winner/P1')!='Winner/P1':
					match={'winner':row.get('Winner/P1','').strip(),'loser':row.get('Loser/P2','').strip(),'result':row.get('Result','').strip(),'map':row.get('Map','').strip(),'region':row.get('Region','').strip(),'winner_kills':self.safe_int(row.get('Winner Kills','0')),'loser_kills':self.safe_int(row.get('Loser Kills','0')),'winner_kdr':self.safe_float(row.get('Winner KDR','0')),'loser_kdr':self.safe_float(row.get('Loser KDR','0')),'outcome':row.get('Outcome','').strip(),'winner_points':self.safe_float(row.get('Winner Points','0')),'loser_points':self.safe_float(row.get('Loser Points','0')),'date':row.get('Date','').strip(),'time':row.get('Time','').strip(),'tournament':row.get('Tournament','').strip(),'week':row.get('Week','').strip(),'season':row.get('Season','').strip()};self.matches.append(match)
					if match['winner']and match['winner']!='[RESIGNED]':self.players.add(match['winner'])
					if match['loser']and match['loser']!='[RESIGNED]':self.players.add(match['loser'])
			self.last_updated=datetime.now();print(f"Loaded {len(self.matches)} matches and {len(self.players)} players");return True
		except Exception as e:print(f"Error loading data: {e}");return False
	def safe_int(self,value):
		try:return int(float(value))if value else 0
		except:return 0
	def safe_float(self,value):
		try:return float(value)if value else .0
		except:return .0
game_data=BlockTanksData()
@bot.event
async def on_ready():print(f"{bot.user} has connected to Discord!");await game_data.load_data();print('Data loaded successfully!')
@bot.command(name='refresh')
async def refresh_data(ctx):
	'Refresh data from the spreadsheet';await ctx.send('🔄 Refreshing data from spreadsheet...');success=await game_data.load_data()
	if success:await ctx.send(f"✅ Data refreshed! Loaded {len(game_data.matches)} matches and {len(game_data.players)} players.\nLast updated: {game_data.last_updated.strftime("%Y-%m-%d %H:%M:%S")}")
	else:await ctx.send('❌ Failed to refresh data. Please try again later.')
@tasks.loop(minutes=5)
async def auto_refresh_data():
    success = await game_data.load_data()
    if success:
        print(f"✅ Auto-refreshed at {datetime.now()}")
    else:
        print("❌ Auto-refresh failed")

@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    await game_data.load_data()
    auto_refresh_data.start()  # Start the auto-refresh loop
    print('Data loaded successfully!')
@bot.command(name='player')
async def player_stats(ctx,*,player_name=None):
	'Get comprehensive stats for a specific player'
	if not player_name:await ctx.send('Please provide a player name: `!player PlayerName`');return
	found_player=None
	for p in game_data.players:
		if p.lower()==player_name.lower():found_player=p;break
	if not found_player:similar=[p for p in game_data.players if player_name.lower()in p.lower()];suggestion_text=f"\nDid you mean: {", ".join(similar[:5])}"if similar else'';await ctx.send(f"Player '{player_name}' not found.{suggestion_text}");return
	wins=losses=draws=0;total_kills=total_deaths=0;total_points=.0;maps_played=Counter();regions_played=Counter();opponents_beaten=Counter();opponents_lost_to=Counter();recent_form=[];kdrs=[];points_per_game=[];kills_per_game=[];tournament_wins=Counter();season_stats=defaultdict(lambda:{'wins':0,'losses':0,'draws':0,'points':0});player_matches=[]
	for match in game_data.matches:
		if match['winner']==found_player or match['loser']==found_player:player_matches.append(match)
	for match in player_matches:
		if match['winner']==found_player:
			if match['outcome']=='Draw':draws+=1;recent_form.append('D')
			else:wins+=1;recent_form.append('W');opponents_beaten[match['loser']]+=1
			total_points+=match['winner_points'];total_kills+=match['winner_kills'];total_deaths+=match['loser_kills'];kdrs.append(match['winner_kdr']);points_per_game.append(match['winner_points']);kills_per_game.append(match['winner_kills'])
			if match['tournament']:tournament_wins[match['tournament']]+=1
		elif match['loser']==found_player:
			if match['outcome']=='Draw':draws+=1;recent_form.append('D')
			else:losses+=1;recent_form.append('L');opponents_lost_to[match['winner']]+=1
			total_points+=match['loser_points'];total_kills+=match['loser_kills'];total_deaths+=match['winner_kills'];kdrs.append(match['loser_kdr']);points_per_game.append(match['loser_points']);kills_per_game.append(match['loser_kills'])
		maps_played[match['map']]+=1;regions_played[match['region']]+=1
		if match['season']:
			season=match['season']
			if match['winner']==found_player:
				if match['outcome']=='Draw':season_stats[season]['draws']+=1
				else:season_stats[season]['wins']+=1
				season_stats[season]['points']+=match['winner_points']
			else:
				if match['outcome']=='Draw':season_stats[season]['draws']+=1
				else:season_stats[season]['losses']+=1
				season_stats[season]['points']+=match['loser_points']
	total_games=wins+losses+draws;kdr=total_kills/max(total_deaths,1);win_rate=wins/max(total_games,1)*100;avg_points=statistics.mean(points_per_game)if points_per_game else 0;avg_kills=statistics.mean(kills_per_game)if kills_per_game else 0;avg_kdr=statistics.mean(kdrs)if kdrs else 0;embed=discord.Embed(title=f"📊 Detailed Stats for {found_player}",color=65280);embed.add_field(name='🏆 Overall Record',value=f"**{wins}W - {losses}L - {draws}D**\nWin Rate: **{win_rate:.1f}%**\nTotal Games: **{total_games}**",inline=True);embed.add_field(name='⚔️ Combat Performance',value=f"**{total_kills}** total kills\n**{total_deaths}** total deaths\n**{kdr:.2f}** overall K/D\n**{avg_kdr:.2f}** avg K/D per game\n**{avg_kills:.1f}** avg kills/game",inline=True);embed.add_field(name='📈 Points & Performance',value=f"**{total_points:.1f}** total points\n**{avg_points:.1f}** avg points/game\n**{max(points_per_game)if points_per_game else 0:.1f}** best game points",inline=True)
	if recent_form:form_display=''.join(recent_form[-10:]);embed.add_field(name='📊 Recent Form (Last 10)',value=f"**{form_display}**",inline=True)
	if maps_played:fav_map=maps_played.most_common(1)[0];embed.add_field(name='🗺️ Favorite Map',value=f"**{fav_map[0]}**\n({fav_map[1]} games)",inline=True)
	if regions_played:main_region=regions_played.most_common(1)[0];embed.add_field(name='🌍 Main Region',value=f"**{main_region[0]}**\n({main_region[1]} games)",inline=True)
	if opponents_beaten:top_victim=opponents_beaten.most_common(1)[0];embed.add_field(name='🎯 Most Defeated',value=f"**{top_victim[0]}**\n({top_victim[1]} times)",inline=True)
	if opponents_lost_to:main_rival=opponents_lost_to.most_common(1)[0];embed.add_field(name='😅 Biggest Rival',value=f"**{main_rival[0]}**\n(lost {main_rival[1]} times)",inline=True)
	if tournament_wins:best_tournament=tournament_wins.most_common(1)[0];embed.add_field(name='🏆 Tournament Success',value=f"**{best_tournament[0]}**\n({best_tournament[1]} wins)",inline=True)
	if season_stats:
		season_text=''
		for(season,stats)in sorted(season_stats.items()):season_text+=f"**{season}**: {stats["wins"]}W-{stats["losses"]}L-{stats["draws"]}D ({stats["points"]:.1f}pts)\n"
		embed.add_field(name='📅 Season Breakdown',value=season_text[:1024],inline=False)
	await ctx.send(embed=embed)
@bot.command(name='leaderboard',aliases=['lb','top'])
async def leaderboard(ctx,stat='points',season=None):
	'Show detailed leaderboard by various stats';valid_stats=['wins','points','kdr','kills','games','winrate','ppg','kpg']
	if stat.lower()not in valid_stats:await ctx.send(f"Invalid stat. Choose from: {", ".join(valid_stats)}");return
	player_stats={}
	for player in game_data.players:
		wins=losses=draws=kills=deaths=0;points=.0;games_played=0
		for match in game_data.matches:
			if season and match.get('season','').lower()!=season.lower():continue
			if match['winner']==player:
				if match['outcome']=='Draw':draws+=1
				else:wins+=1
				points+=match['winner_points'];kills+=match['winner_kills'];deaths+=match['loser_kills'];games_played+=1
			elif match['loser']==player:
				if match['outcome']=='Draw':draws+=1
				else:losses+=1
				points+=match['loser_points'];kills+=match['loser_kills'];deaths+=match['winner_kills'];games_played+=1
		total_games=wins+losses+draws
		if total_games>0:kdr=kills/max(deaths,1);winrate=wins/total_games*100;ppg=points/total_games;kpg=kills/total_games;player_stats[player]={'wins':wins,'points':points,'kdr':kdr,'kills':kills,'games':total_games,'winrate':winrate,'ppg':ppg,'kpg':kpg}
	stat_lower=stat.lower();sorted_players=sorted(player_stats.items(),key=lambda x:x[1][stat_lower],reverse=True);stat_names={'wins':'🏆 Wins Leaderboard','points':'📈 Points Leaderboard','kdr':'⚔️ K/D Ratio Leaderboard','kills':'💀 Kills Leaderboard','games':'🎮 Games Played Leaderboard','winrate':'📊 Win Rate Leaderboard','ppg':'📈 Points Per Game Leaderboard','kpg':'⚔️ Kills Per Game Leaderboard'};title=stat_names[stat_lower]
	if season:title+=f" (Season: {season})"
	embed=discord.Embed(title=title,color=16766720);leaderboard_text=''
	for(i,(player,stats))in enumerate(sorted_players[:20],1):
		medal='🥇'if i==1 else'🥈'if i==2 else'🥉'if i==3 else f"{i}."
		if stat_lower in['points','ppg','kpg']:value=f"{stats[stat_lower]:.1f}"
		elif stat_lower in['kdr','winrate']:
			value=f"{stats[stat_lower]:.2f}"
			if stat_lower=='winrate':value+='%'
		else:value=str(int(stats[stat_lower]))
		games=stats['games'];leaderboard_text+=f"{medal} **{player}** - {value} ({games} games)\n"
	embed.description=leaderboard_text;await ctx.send(embed=embed)
@bot.command(name='match')
async def recent_matches(ctx,*,player_name=None):
	'Show detailed recent matches';matches_to_show=game_data.matches[-15:]
	if player_name:
		found_player=None
		for p in game_data.players:
			if p.lower()==player_name.lower():found_player=p;break
		if not found_player:await ctx.send(f"Player '{player_name}' not found.");return
		player_matches=[]
		for match in game_data.matches:
			if match['winner']==found_player or match['loser']==found_player:player_matches.append(match)
		matches_to_show=player_matches[-15:];embed_title=f"📝 Recent matches for {found_player}"
	else:embed_title='📝 Recent matches (All Players)'
	embed=discord.Embed(title=embed_title,color=39423);match_text=''
	for match in reversed(matches_to_show):
		result=match['result'];map_name=match['map'];region=match['region'];winner_kills=match['winner_kills'];loser_kills=match['loser_kills'];winner_points=match['winner_points'];loser_points=match['loser_points'];date=match.get('date','');tournament=match.get('tournament','');kill_info=f"({winner_kills}-{loser_kills})";points_info=f"[{winner_points:.1f}-{loser_points:.1f}pts]"
		if match['outcome']=='Draw':match_line=f"🤝 **{match["winner"]}** vs **{match["loser"]}** {kill_info}\n"
		else:match_line=f"🏆 **{match["winner"]}** beat **{match["loser"]}** {kill_info}\n"
		match_line+=f"   📍 {map_name} ({region}) {points_info}"
		if tournament:match_line+=f" 🏆{tournament}"
		if date:match_line+=f" 📅{date}"
		match_line+='\n\n';match_text+=match_line
	if not match_text:match_text='No matches found.'
	embed.description=match_text[:4000];await ctx.send(embed=embed)
@bot.command(name='map')
async def map_stats(ctx,*,map_name=None):
	'Show comprehensive map statistics'
	if not map_name:
		maps=Counter()
		for match in game_data.matches:
			if match['map']:maps[match['map']]+=1
		embed=discord.Embed(title='🗺️ Map Statistics Overview',color=65433);map_list=''
		for(map_name,count)in maps.most_common():map_matches=[m for m in game_data.matches if m['map']==map_name];total_kills=sum(m['winner_kills']+m['loser_kills']for m in map_matches);avg_kills=total_kills/count if count>0 else 0;avg_points=sum(m['winner_points']+m['loser_points']for m in map_matches)/count if count>0 else 0;map_list+=f"**{map_name}** - {count} matches\n";map_list+=f"   ⚔️ {avg_kills:.1f} avg kills/game | 📈 {avg_points:.1f} avg points/game\n\n"
		embed.description=map_list;await ctx.send(embed=embed);return
	map_matches=[m for m in game_data.matches if m['map'].lower()==map_name.lower()]
	if not map_matches:await ctx.send(f"No matches found on map '{map_name}'");return
	actual_map_name=map_matches[0]['map'];total_matches=len(map_matches);total_kills=sum(m['winner_kills']+m['loser_kills']for m in map_matches);total_points=sum(m['winner_points']+m['loser_points']for m in map_matches);avg_kills=total_kills/total_matches;avg_points=total_points/total_matches;regions=Counter(m['region']for m in map_matches);players=Counter();player_wins=Counter();tournaments=Counter();outcomes=Counter()
	for match in map_matches:
		if match['winner']!='[RESIGNED]':players[match['winner']]+=1;player_wins[match['winner']]+=1 if match['outcome']!='Draw'else 0
		if match['loser']!='[RESIGNED]':players[match['loser']]+=1
		if match['tournament']:tournaments[match['tournament']]+=1
		outcomes[match['outcome']]+=1
	player_winrates={}
	for(player,games)in players.most_common(10):wins=player_wins.get(player,0);winrate=wins/games*100 if games>0 else 0;player_winrates[player]=wins,games,winrate
	embed=discord.Embed(title=f"🗺️ {actual_map_name} - Detailed Analysis",color=65433);embed.add_field(name='📊 Match Overview',value=f"**{total_matches}** total matches\n**{avg_kills:.1f}** avg kills per game\n**{avg_points:.1f}** avg points per game",inline=True)
	if regions:top_regions=regions.most_common(3);region_text='\n'.join([f"**{region}**: {count} games"for(region,count)in top_regions]);embed.add_field(name='🌍 Regional Play',value=region_text,inline=True)
	if outcomes:outcome_text='\n'.join([f"**{outcome or"Regular"}**: {count}"for(outcome,count)in outcomes.most_common()]);embed.add_field(name='🎯 Match Outcomes',value=outcome_text,inline=True)
	if player_winrates:
		performer_text=''
		for(player,(wins,games,winrate))in list(player_winrates.items())[:5]:
			if games>=3:performer_text+=f"**{player}**: {wins}W/{games}G ({winrate:.1f}%)\n"
		if performer_text:embed.add_field(name='👑 Top Performers (3+ games)',value=performer_text,inline=False)
	if tournaments:tournament_text='\n'.join([f"**{t}**: {c} matches"for(t,c)in tournaments.most_common(3)]);embed.add_field(name='🏆 Tournament Activity',value=tournament_text,inline=True)
	await ctx.send(embed=embed)
@bot.command(name='vs')
async def head_to_head(ctx,player1,*,player2):
	'Detailed head-to-head comparison';found_p1=found_p2=None
	for p in game_data.players:
		if p.lower()==player1.lower():found_p1=p
		if p.lower()==player2.lower():found_p2=p
	if not found_p1:await ctx.send(f"Player '{player1}' not found.");return
	if not found_p2:await ctx.send(f"Player '{player2}' not found.");return
	h2h_matches=[]
	for match in game_data.matches:
		if match['winner']==found_p1 and match['loser']==found_p2 or match['winner']==found_p2 and match['loser']==found_p1:h2h_matches.append(match)
	if not h2h_matches:await ctx.send(f"No matches found between {found_p1} and {found_p2}");return
	p1_wins=p1_kills=p1_deaths=p1_points=0;p2_wins=p2_kills=p2_deaths=p2_points=0;draws=0;maps_played=Counter();recent_matches=[]
	for match in h2h_matches:
		maps_played[match['map']]+=1
		if match['outcome']=='Draw':draws+=1
		elif match['winner']==found_p1:p1_wins+=1
		else:p2_wins+=1
		if match['winner']==found_p1:p1_kills+=match['winner_kills'];p1_deaths+=match['loser_kills'];p1_points+=match['winner_points'];p2_kills+=match['loser_kills'];p2_deaths+=match['winner_kills'];p2_points+=match['loser_points'];recent_matches.append(f"W vs {found_p2}")
		else:p2_kills+=match['winner_kills'];p2_deaths+=match['loser_kills'];p2_points+=match['winner_points'];p1_kills+=match['loser_kills'];p1_deaths+=match['winner_kills'];p1_points+=match['loser_points'];recent_matches.append(f"L vs {found_p2}")
	embed=discord.Embed(title=f"⚔️ {found_p1} vs {found_p2} - Head to Head",color=16739229);total_games=len(h2h_matches);p1_winrate=p1_wins/max(total_games-draws,1)*100;p2_winrate=p2_wins/max(total_games-draws,1)*100;embed.add_field(name='🏆 Head-to-Head Record',value=f"**{found_p1}**: {p1_wins}W ({p1_winrate:.1f}%)\n**{found_p2}**: {p2_wins}W ({p2_winrate:.1f}%)\n**Draws**: {draws}\n**Total Games**: {total_games}",inline=True);p1_kdr=p1_kills/max(p1_deaths,1);p2_kdr=p2_kills/max(p2_deaths,1);embed.add_field(name='💀 Combat Stats',value=f"**{found_p1}**: {p1_kills}K/{p1_deaths}D ({p1_kdr:.2f})\n**{found_p2}**: {p2_kills}K/{p2_deaths}D ({p2_kdr:.2f})",inline=True);p1_ppg=p1_points/total_games;p2_ppg=p2_points/total_games;embed.add_field(name='📈 Points Performance',value=f"**{found_p1}**: {p1_points:.1f} total ({p1_ppg:.1f}/game)\n**{found_p2}**: {p2_points:.1f} total ({p2_ppg:.1f}/game)",inline=True)
	if maps_played:map_text='\n'.join([f"**{map_name}**: {count} games"for(map_name,count)in maps_played.most_common(5)]);embed.add_field(name='🗺️ Maps Played',value=map_text,inline=True)
	recent_form=recent_matches[-5:]
	if recent_form:form_display=' → '.join([result.split()[0]for result in recent_form]);embed.add_field(name='📊 Recent Form (Last 5)',value=f"**{found_p1}**: {form_display}",inline=True)
	await ctx.send(embed=embed)
@bot.command(name='tournament',aliases=['tourney'])
async def tournament_stats(ctx,*,tournament_name=None):
	'Show tournament statistics and leaderboards'
	if not tournament_name:
		tournaments=Counter()
		for match in game_data.matches:
			if match.get('tournament'):tournaments[match['tournament']]+=1
		embed=discord.Embed(title='🏆 Tournament Overview',color=16766720)
		if tournaments:
			tourney_text=''
			for(tourney,matches)in tournaments.most_common():tourney_text+=f"**{tourney}**: {matches} matches\n"
			embed.add_field(name='Available Tournaments',value=tourney_text,inline=False)
		else:embed.description='No tournament data available.'
		await ctx.send(embed=embed);return
	tournament_matches=[m for m in game_data.matches if m.get('tournament','').lower()==tournament_name.lower()]
	if not tournament_matches:await ctx.send(f"No matches found for tournament '{tournament_name}'");return
	actual_tournament_name=tournament_matches[0]['tournament'];participants=set();player_stats=defaultdict(lambda:{'wins':0,'losses':0,'draws':0,'kills':0,'deaths':0,'points':0})
	for match in tournament_matches:
		if match['winner']!='[RESIGNED]':
			participants.add(match['winner'])
			if match['outcome']=='Draw':player_stats[match['winner']]['draws']+=1
			else:player_stats[match['winner']]['wins']+=1
			player_stats[match['winner']]['kills']+=match['winner_kills'];player_stats[match['winner']]['deaths']+=match['loser_kills'];player_stats[match['winner']]['points']+=match['winner_points']
		if match['loser']!='[RESIGNED]':
			participants.add(match['loser'])
			if match['outcome']=='Draw':player_stats[match['loser']]['draws']+=1
			else:player_stats[match['loser']]['losses']+=1
			player_stats[match['loser']]['kills']+=match['loser_kills'];player_stats[match['loser']]['deaths']+=match['winner_kills'];player_stats[match['loser']]['points']+=match['loser_points']
	sorted_players=sorted(player_stats.items(),key=lambda x:(x[1]['wins'],x[1]['points']),reverse=True);embed=discord.Embed(title=f"🏆 {actual_tournament_name} Statistics",color=16766720);embed.add_field(name='📊 Tournament Overview',value=f"**{len(tournament_matches)}** total matches\n**{len(participants)}** participants\n**{sum(m["winner_kills"]+m["loser_kills"]for m in tournament_matches)}** total kills",inline=True);leaderboard_text=''
	for(i,(player,stats))in enumerate(sorted_players[:10],1):medal='🥇'if i==1 else'🥈'if i==2 else'🥉'if i==3 else f"{i}.";total_games=stats['wins']+stats['losses']+stats['draws'];kdr=stats['kills']/max(stats['deaths'],1);leaderboard_text+=f"{medal} **{player}** - {stats["wins"]}W/{stats["losses"]}L/{stats["draws"]}D ";leaderboard_text+=f"({stats["points"]:.1f}pts, {kdr:.2f} K/D)\n"
	embed.add_field(name='🏆 Tournament Leaderboard',value=leaderboard_text,inline=False);await ctx.send(embed=embed)
@bot.command(name='season')
async def season_stats(ctx,*,season_name=None):
	'Show season statistics and analysis'
	if not season_name:
		seasons=Counter()
		for match in game_data.matches:
			if match.get('season'):seasons[match['season']]+=1
		embed=discord.Embed(title='📅 Season Overview',color=10040012)
		if seasons:
			season_text=''
			for(season,matches)in seasons.most_common():season_text+=f"**{season}**: {matches} matches\n"
			embed.add_field(name='Available Seasons',value=season_text,inline=False)
		else:embed.description='No season data available.'
		await ctx.send(embed=embed);return
	season_matches=[m for m in game_data.matches if m.get('season','').lower()==season_name.lower()]
	if not season_matches:await ctx.send(f"No matches found for season '{season_name}'");return
	actual_season_name=season_matches[0]['season'];participants=set();player_stats=defaultdict(lambda:{'wins':0,'losses':0,'draws':0,'kills':0,'deaths':0,'points':0,'games':0});maps_played=Counter();weekly_activity=Counter()
	for match in season_matches:
		maps_played[match['map']]+=1
		if match.get('week'):weekly_activity[match['week']]+=1
		for(player_key,opponent_key)in[('winner','loser'),('loser','winner')]:
			player=match[player_key]
			if player!='[RESIGNED]':
				participants.add(player);player_stats[player]['games']+=1
				if player_key=='winner':
					if match['outcome']=='Draw':player_stats[player]['draws']+=1
					else:player_stats[player]['wins']+=1
					player_stats[player]['kills']+=match['winner_kills'];player_stats[player]['deaths']+=match['loser_kills'];player_stats[player]['points']+=match['winner_points']
				else:
					if match['outcome']=='Draw':player_stats[player]['draws']+=1
					else:player_stats[player]['losses']+=1
					player_stats[player]['kills']+=match['loser_kills'];player_stats[player]['deaths']+=match['winner_kills'];player_stats[player]['points']+=match['loser_points']
	for(player,stats)in player_stats.items():stats['winrate']=stats['wins']/max(stats['games']-stats['draws'],1)*100;stats['kdr']=stats['kills']/max(stats['deaths'],1);stats['ppg']=stats['points']/max(stats['games'],1)
	sorted_players=sorted(player_stats.items(),key=lambda x:x[1]['points'],reverse=True);embed=discord.Embed(title=f"📅 {actual_season_name} Season Analysis",color=10040012);total_kills=sum(m['winner_kills']+m['loser_kills']for m in season_matches);total_points=sum(m['winner_points']+m['loser_points']for m in season_matches);embed.add_field(name='📊 Season Overview',value=f"**{len(season_matches)}** matches played\n**{len(participants)}** active players\n**{total_kills}** total eliminations\n**{total_points:.1f}** total points awarded",inline=True)
	if maps_played:top_maps=maps_played.most_common(3);map_text='\n'.join([f"**{map_name}**: {count}"for(map_name,count)in top_maps]);embed.add_field(name='🗺️ Most Played Maps',value=map_text,inline=True)
	if weekly_activity:week_text='\n'.join([f"**Week {week}**: {matches}"for(week,matches)in sorted(weekly_activity.items())]);embed.add_field(name='📈 Weekly Activity',value=week_text[:1024],inline=True)
	leaderboard_text=''
	for(i,(player,stats))in enumerate(sorted_players[:15],1):medal='🥇'if i==1 else'🥈'if i==2 else'🥉'if i==3 else f"{i}.";leaderboard_text+=f"{medal} **{player}** - {stats["points"]:.1f}pts ";leaderboard_text+=f"({stats["wins"]}W-{stats["losses"]}L-{stats["draws"]}D, ";leaderboard_text+=f"{stats["winrate"]:.1f}% WR, {stats["kdr"]:.2f} K/D)\n"
	embed.add_field(name='🏆 Season Leaderboard',value=leaderboard_text,inline=False);await ctx.send(embed=embed)
@bot.command(name='compare')
async def compare_players(ctx,player1,*,player2):
	'Comprehensive comparison between two players';found_p1=found_p2=None
	for p in game_data.players:
		if p.lower()==player1.lower():found_p1=p
		if p.lower()==player2.lower():found_p2=p
	if not found_p1:await ctx.send(f"Player '{player1}' not found.");return
	if not found_p2:await ctx.send(f"Player '{player2}' not found.");return
	players_stats={}
	for player in[found_p1,found_p2]:
		stats={'wins':0,'losses':0,'draws':0,'kills':0,'deaths':0,'points':0,'games':0,'maps':Counter(),'opponents_beaten':Counter(),'recent_form':[]}
		for match in game_data.matches:
			if match['winner']==player:
				if match['outcome']=='Draw':stats['draws']+=1;stats['recent_form'].append('D')
				else:stats['wins']+=1;stats['recent_form'].append('W');stats['opponents_beaten'][match['loser']]+=1
				stats['kills']+=match['winner_kills'];stats['deaths']+=match['loser_kills'];stats['points']+=match['winner_points'];stats['games']+=1;stats['maps'][match['map']]+=1
			elif match['loser']==player:
				if match['outcome']=='Draw':stats['draws']+=1;stats['recent_form'].append('D')
				else:stats['losses']+=1;stats['recent_form'].append('L')
				stats['kills']+=match['loser_kills'];stats['deaths']+=match['winner_kills'];stats['points']+=match['loser_points'];stats['games']+=1;stats['maps'][match['map']]+=1
		stats['winrate']=stats['wins']/max(stats['games']-stats['draws'],1)*100;stats['kdr']=stats['kills']/max(stats['deaths'],1);stats['ppg']=stats['points']/max(stats['games'],1);stats['kpg']=stats['kills']/max(stats['games'],1);players_stats[player]=stats
	p1_stats=players_stats[found_p1];p2_stats=players_stats[found_p2];embed=discord.Embed(title=f"📊 Player Comparison: {found_p1} vs {found_p2}",color=52945);embed.add_field(name='🏆 Overall Record',value=f"**{found_p1}**: {p1_stats["wins"]}W-{p1_stats["losses"]}L-{p1_stats["draws"]}D ({p1_stats["winrate"]:.1f}%)\n**{found_p2}**: {p2_stats["wins"]}W-{p2_stats["losses"]}L-{p2_stats["draws"]}D ({p2_stats["winrate"]:.1f}%)",inline=False);embed.add_field(name='⚔️ Combat Stats',value=f"**{found_p1}**: {p1_stats["kills"]}K/{p1_stats["deaths"]}D ({p1_stats["kdr"]:.2f} K/D)\n**{found_p2}**: {p2_stats["kills"]}K/{p2_stats["deaths"]}D ({p2_stats["kdr"]:.2f} K/D)",inline=True);embed.add_field(name='📈 Performance',value=f"**{found_p1}**: {p1_stats["ppg"]:.1f} PPG, {p1_stats["kpg"]:.1f} KPG\n**{found_p2}**: {p2_stats["ppg"]:.1f} PPG, {p2_stats["kpg"]:.1f} KPG",inline=True);embed.add_field(name='🎮 Activity',value=f"**{found_p1}**: {p1_stats["games"]} total games\n**{found_p2}**: {p2_stats["games"]} total games",inline=True);p1_form=''.join(p1_stats['recent_form'][-10:]);p2_form=''.join(p2_stats['recent_form'][-10:]);embed.add_field(name='📊 Recent Form (Last 10)',value=f"**{found_p1}**: {p1_form}\n**{found_p2}**: {p2_form}",inline=False);p1_fav_map=p1_stats['maps'].most_common(1)[0]if p1_stats['maps']else('None',0);p2_fav_map=p2_stats['maps'].most_common(1)[0]if p2_stats['maps']else('None',0);embed.add_field(name='🗺️ Favorite Maps',value=f"**{found_p1}**: {p1_fav_map[0]} ({p1_fav_map[1]} games)\n**{found_p2}**: {p2_fav_map[0]} ({p2_fav_map[1]} games)",inline=True);p1_victim=p1_stats['opponents_beaten'].most_common(1)[0]if p1_stats['opponents_beaten']else('None',0);p2_victim=p2_stats['opponents_beaten'].most_common(1)[0]if p2_stats['opponents_beaten']else('None',0);embed.add_field(name='🎯 Most Defeated',value=f"**{found_p1}**: {p1_victim[0]} ({p1_victim[1]}x)\n**{found_p2}**: {p2_victim[0]} ({p2_victim[1]}x)",inline=True);await ctx.send(embed=embed)
@bot.command(name='rankings')
async def power_rankings(ctx,season=None):
	'Show comprehensive power rankings with multiple metrics';player_stats={}
	for player in game_data.players:
		stats={'wins':0,'losses':0,'draws':0,'kills':0,'deaths':0,'points':0,'games':0}
		for match in game_data.matches:
			if season and match.get('season','').lower()!=season.lower():continue
			if match['winner']==player:
				if match['outcome']=='Draw':stats['draws']+=1
				else:stats['wins']+=1
				stats['points']+=match['winner_points'];stats['kills']+=match['winner_kills'];stats['deaths']+=match['loser_kills'];stats['games']+=1
			elif match['loser']==player:
				if match['outcome']=='Draw':stats['draws']+=1
				else:stats['losses']+=1
				stats['points']+=match['loser_points'];stats['kills']+=match['loser_kills'];stats['deaths']+=match['winner_kills'];stats['games']+=1
		if stats['games']>=5:stats['winrate']=stats['wins']/max(stats['games']-stats['draws'],1)*100;stats['kdr']=stats['kills']/max(stats['deaths'],1);stats['ppg']=stats['points']/stats['games'];power_rating=stats['winrate']*.3+stats['kdr']*20*.25+stats['ppg']*.25+min(stats['games']/20,1)*20*.2;stats['power_rating']=power_rating;player_stats[player]=stats
	sorted_players=sorted(player_stats.items(),key=lambda x:x[1]['power_rating'],reverse=True);title='🏆 Power Rankings'
	if season:title+=f" (Season: {season})"
	embed=discord.Embed(title=title,color=16716947);embed.add_field(name='📊 Ranking Formula',value='Win Rate (30%) + K/D (25%) + PPG (25%) + Activity (20%)',inline=False);rankings_text=''
	for(i,(player,stats))in enumerate(sorted_players[:15],1):medal='🥇'if i==1 else'🥈'if i==2 else'🥉'if i==3 else f"{i}.";rankings_text+=f"{medal} **{player}** - {stats["power_rating"]:.1f}\n";rankings_text+=f"   {stats["winrate"]:.1f}% WR | {stats["kdr"]:.2f} K/D | ";rankings_text+=f"{stats["ppg"]:.1f} PPG | {stats["games"]} games\n\n"
	embed.add_field(name='🏆 Current Rankings',value=rankings_text,inline=False);await ctx.send(embed=embed)
@bot.command(name='help')
async def help_command(ctx):'Show all available commands with detailed descriptions';embed=discord.Embed(title='🤖 BlockTanks League Bot - Complete Command Guide',color=7506394);commands_text='\n**Player Commands:**\n`!player <name>` - Comprehensive player statistics and analysis\n`!compare <player1> <player2>` - Detailed comparison between two players\n`!vs <player1> <player2>` - Head-to-head matchup analysis\n\n**Leaderboards & Rankings:**\n`!leaderboard [stat] [season]` - Show leaderboards (wins/points/kdr/kills/games/winrate/ppg/kpg)\n`!rankings [season]` - Power rankings with composite scoring\n\n**Match & Map Analysis:**\n`!match [player]` - Recent matches with detailed stats\n`!map [name]` - Comprehensive map statistics and analysis\n\n**Competition Data:**\n`!tournament [name]` - Tournament statistics and leaderboards\n`!season [name]` - Season analysis and standings\n\n**System Commands:**\n`!refresh` - Refresh data from spreadsheet\n`!help` - Show this help message\n    ';embed.description=commands_text;embed.add_field(name='💡 Pro Tips:',value='• Use `!leaderboard winrate` for win percentage rankings\n• Try `!player YourName` to see your detailed stats\n• Use `!map` without a name to see all available maps\n• Add season names to filter leaderboards by season',inline=False);embed.add_field(name='📊 Available Stats:',value='**wins** - Total wins | **points** - Total points | **kdr** - Kill/Death ratio\n**kills** - Total kills | **games** - Games played | **winrate** - Win percentage\n**ppg** - Points per game | **kpg** - Kills per game',inline=False);embed.add_field(name='🔍 Examples:',value='`!player Giant_Professor` - Get detailed player stats\n`!leaderboard points Season1` - Season 1 points leaderboard\n`!vs blu NYS_Lask` - Head-to-head comparison\n`!compare PlayerA PlayerB` - Full player comparison\n`!tournament WeeklyTourney` - Tournament analysis',inline=False);await ctx.send(embed=embed)
@bot.command(name='stats')
async def global_stats(ctx):
	'Show overall league statistics'
	if not game_data.matches:await ctx.send('No data available. Use `!refresh` to load data.');return
	total_matches=len(game_data.matches);total_players=len(game_data.players);total_kills=sum(m['winner_kills']+m['loser_kills']for m in game_data.matches);total_points=sum(m['winner_points']+m['loser_points']for m in game_data.matches);player_games=Counter()
	for match in game_data.matches:
		if match['winner']!='[RESIGNED]':player_games[match['winner']]+=1
		if match['loser']!='[RESIGNED]':player_games[match['loser']]+=1
	map_popularity=Counter(m['map']for m in game_data.matches if m['map']);region_dist=Counter(m['region']for m in game_data.matches if m['region']);embed=discord.Embed(title='📊 BlockTanks League - Global Statistics',color=3329330);embed.add_field(name='🎮 Overall Activity',value=f"**{total_matches:,}** total matches\n**{total_players}** registered players\n**{total_kills:,}** total eliminations\n**{total_points:,.1f}** total points awarded",inline=True)
	if player_games:most_active=player_games.most_common(1)[0];embed.add_field(name='👑 Most Active Player',value=f"**{most_active[0]}**\n{most_active[1]} games played",inline=True)
	avg_kills_per_game=total_kills/total_matches if total_matches>0 else 0;avg_points_per_game=total_points/total_matches if total_matches>0 else 0;embed.add_field(name='📈 Averages',value=f"**{avg_kills_per_game:.1f}** kills per match\n**{avg_points_per_game:.1f}** points per match",inline=True)
	if map_popularity:pop_map=map_popularity.most_common(1)[0];embed.add_field(name='🗺️ Most Popular Map',value=f"**{pop_map[0]}**\n{pop_map[1]} matches ({pop_map[1]/total_matches*100:.1f}%)",inline=True)
	if region_dist:top_regions=region_dist.most_common(3);region_text='\n'.join([f"**{region}**: {count}"for(region,count)in top_regions]);embed.add_field(name='🌍 Top Regions',value=region_text,inline=True)
	if game_data.last_updated:embed.add_field(name='🔄 Data Status',value=f"Last updated:\n{game_data.last_updated.strftime("%Y-%m-%d %H:%M:%S")}",inline=True)
	await ctx.send(embed=embed)
if __name__=='__main__':bot.run(os.getenv("DISCORD_TOKEN"))
