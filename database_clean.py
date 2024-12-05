import pandas as pd
import sqlite3

# Enable foreign key support
conn = sqlite3.connect('ufc_database.db')
conn.execute("PRAGMA foreign_keys = ON")

# Read from existing database
df = pd.read_sql('SELECT * FROM ufc_data', conn)
cursor = conn.cursor()

# Drop existing tables if they exist
cursor.execute("DROP TABLE IF EXISTS FightDetails")
cursor.execute("DROP TABLE IF EXISTS FightOdds")
cursor.execute("DROP TABLE IF EXISTS FighterRanks")
cursor.execute("DROP TABLE IF EXISTS FighterStats")
cursor.execute("DROP TABLE IF EXISTS Fights")
cursor.execute("DROP TABLE IF EXISTS Fighters")

# Create Fighters table with FighterName as primary key
cursor.execute('''
CREATE TABLE Fighters (
    FighterName TEXT PRIMARY KEY,
    Stance TEXT,
    HeightCms REAL,
    ReachCms REAL,
    WeightLbs INTEGER,
    Age INTEGER
)
''')

# Create Fights table with composite primary key
cursor.execute('''
CREATE TABLE Fights (
    RedFighter TEXT,
    BlueFighter TEXT,
    Date TEXT,
    Location TEXT,
    Country TEXT,
    Winner TEXT,
    TitleBout INTEGER,
    WeightClass TEXT,
    Gender TEXT,
    NumberOfRounds INTEGER,
    EmptyArena REAL,
    TotalFightTimeSecs REAL,
    PRIMARY KEY (RedFighter, BlueFighter, Date),
    FOREIGN KEY (RedFighter) REFERENCES Fighters(FighterName),
    FOREIGN KEY (BlueFighter) REFERENCES Fighters(FighterName)
)
''')

# Create FighterStats table
cursor.execute('''
CREATE TABLE FighterStats (
    FighterName TEXT PRIMARY KEY,
    CurrentLoseStreak INTEGER,
    CurrentWinStreak INTEGER,
    Draws INTEGER,
    AvgSigStrLanded REAL,
    AvgSigStrPct REAL,
    AvgSubAtt REAL,
    AvgTDLanded REAL,
    AvgTDPct REAL,
    LongestWinStreak INTEGER,
    Losses INTEGER,
    TotalRoundsFought INTEGER,
    TotalTitleBouts INTEGER,
    WinsByDecisionMajority INTEGER,
    WinsByDecisionSplit INTEGER,
    WinsByDecisionUnanimous INTEGER,
    WinsByKO INTEGER,
    WinsBySubmission INTEGER,
    WinsByTKODoctorStoppage INTEGER,
    Wins INTEGER,
    FOREIGN KEY (FighterName) REFERENCES Fighters(FighterName)
)
''')

# Create FightOdds table
cursor.execute('''
CREATE TABLE FightOdds (
    RedFighter TEXT,
    BlueFighter TEXT,
    Date TEXT,
    RedOdds REAL,
    BlueOdds REAL,
    RedExpectedValue REAL,
    BlueExpectedValue REAL,
    RedDecOdds REAL,
    BlueDecOdds REAL,
    RSubOdds REAL,
    BSubOdds REAL,
    RKOOdds REAL,
    BKOOdds REAL,
    PRIMARY KEY (RedFighter, BlueFighter, Date),
    FOREIGN KEY (RedFighter, BlueFighter, Date) REFERENCES Fights(RedFighter, BlueFighter, Date)
)
''')

# Create FighterRanks table
cursor.execute('''
CREATE TABLE FighterRanks (
    FighterName TEXT PRIMARY KEY,
    MatchWCRank REAL,
    FlyweightRank REAL,
    FeatherweightRank REAL,
    StrawweightRank REAL,
    BantamweightRank REAL,
    HeavyweightRank REAL,
    LightHeavyweightRank REAL,
    MiddleweightRank REAL,
    WelterweightRank REAL,
    LightweightRank REAL,
    PFPRank REAL,
    FOREIGN KEY (FighterName) REFERENCES Fighters(FighterName)
)
''')

# Create FightDetails table
cursor.execute('''
CREATE TABLE FightDetails (
    RedFighter TEXT,
    BlueFighter TEXT,
    Date TEXT,
    Finish TEXT,
    FinishDetails TEXT,
    FinishRound REAL,
    FinishRoundTime TEXT,
    PRIMARY KEY (RedFighter, BlueFighter, Date),
    FOREIGN KEY (RedFighter, BlueFighter, Date) REFERENCES Fights(RedFighter, BlueFighter, Date)
)
''')

# Insert Fighters data first
fighters_columns = ['FighterName', 'Stance', 'HeightCms', 'ReachCms', 'WeightLbs', 'Age']

# Combine and deduplicate fighter data
red_fighters = pd.DataFrame({
    'FighterName': df['RedFighter'],
    'Stance': df['RedStance'],
    'HeightCms': df['RedHeightCms'],
    'ReachCms': df['RedReachCms'],
    'WeightLbs': df['RedWeightLbs'],
    'Age': df['RedAge']
})

blue_fighters = pd.DataFrame({
    'FighterName': df['BlueFighter'],
    'Stance': df['BlueStance'],
    'HeightCms': df['BlueHeightCms'],
    'ReachCms': df['BlueReachCms'],
    'WeightLbs': df['BlueWeightLbs'],
    'Age': df['BlueAge']
})

fighters_df = pd.concat([red_fighters, blue_fighters]).drop_duplicates(subset=['FighterName'])

# Insert fighters
for _, fighter in fighters_df.iterrows():
    cursor.execute('''
    INSERT INTO Fighters (FighterName, Stance, HeightCms, ReachCms, WeightLbs, Age)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (fighter['FighterName'], fighter['Stance'], fighter['HeightCms'], 
          fighter['ReachCms'], fighter['WeightLbs'], fighter['Age']))

# Insert Fights and related data
for _, fight in df.iterrows():
    # Insert fight
    cursor.execute('''
    INSERT INTO Fights (RedFighter, BlueFighter, Date, Location, Country, 
                       Winner, TitleBout, WeightClass, Gender, NumberOfRounds, 
                       EmptyArena, TotalFightTimeSecs)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        fight['RedFighter'], fight['BlueFighter'], fight['Date'],
        fight['Location'], fight['Country'], fight['Winner'],
        fight['TitleBout'], fight['WeightClass'], fight['Gender'],
        fight['NumberOfRounds'], fight['EmptyArena'], fight['TotalFightTimeSecs']
    ))
    
    # Insert fight odds
    cursor.execute('''
    INSERT INTO FightOdds (RedFighter, BlueFighter, Date, RedOdds, BlueOdds,
                          RedExpectedValue, BlueExpectedValue, RedDecOdds, 
                          BlueDecOdds, RSubOdds, BSubOdds, RKOOdds, BKOOdds)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        fight['RedFighter'], fight['BlueFighter'], fight['Date'],
        fight['RedOdds'], fight['BlueOdds'], fight['RedExpectedValue'],
        fight['BlueExpectedValue'], fight['RedDecOdds'], fight['BlueDecOdds'],
        fight['RSubOdds'], fight['BSubOdds'], fight['RKOOdds'], fight['BKOOdds']
    ))
    
    # Insert fight details
    cursor.execute('''
    INSERT INTO FightDetails (RedFighter, BlueFighter, Date, Finish,
                             FinishDetails, FinishRound, FinishRoundTime)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        fight['RedFighter'], fight['BlueFighter'], fight['Date'],
        fight['Finish'], fight['FinishDetails'], fight['FinishRound'],
        fight['FinishRoundTime']
    ))

# Insert fighter stats (using last known stats for each fighter)
for _, group in df.groupby('RedFighter').last().iterrows():
    cursor.execute('''
    INSERT OR REPLACE INTO FighterStats (
        FighterName, CurrentLoseStreak, CurrentWinStreak, Draws,
        AvgSigStrLanded, AvgSigStrPct, AvgSubAtt, AvgTDLanded,
        AvgTDPct, LongestWinStreak, Losses, TotalRoundsFought,
        TotalTitleBouts, WinsByDecisionMajority, WinsByDecisionSplit,
        WinsByDecisionUnanimous, WinsByKO, WinsBySubmission,
        WinsByTKODoctorStoppage, Wins
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        group.name,  # RedFighter name
        group['RedCurrentLoseStreak'],
        group['RedCurrentWinStreak'],
        group['RedDraws'],
        group['RedAvgSigStrLanded'],
        group['RedAvgSigStrPct'],
        group['RedAvgSubAtt'],
        group['RedAvgTDLanded'],
        group['RedAvgTDPct'],
        group['RedLongestWinStreak'],
        group['RedLosses'],
        group['RedTotalRoundsFought'],
        group['RedTotalTitleBouts'],
        group['RedWinsByDecisionMajority'],
        group['RedWinsByDecisionSplit'],
        group['RedWinsByDecisionUnanimous'],
        group['RedWinsByKO'],
        group['RedWinsBySubmission'],
        group['RedWinsByTKODoctorStoppage'],
        group['RedWins']
    ))

# Insert fighter ranks (using last known ranks for each fighter)
for _, group in df.groupby('RedFighter').last().iterrows():
    cursor.execute('''
    INSERT OR REPLACE INTO FighterRanks (
        FighterName, MatchWCRank, FlyweightRank, FeatherweightRank,
        StrawweightRank, BantamweightRank, HeavyweightRank,
        LightHeavyweightRank, MiddleweightRank, WelterweightRank,
        LightweightRank, PFPRank
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        group.name,  # RedFighter name
        group['RMatchWCRank'],
        group['RWFlyweightRank'],
        group['RWFeatherweightRank'],
        group['RWStrawweightRank'],
        group['RWBantamweightRank'],
        group['RHeavyweightRank'],
        group['RLightHeavyweightRank'],
        group['RMiddleweightRank'],
        group['RWelterweightRank'],
        group['RLightweightRank'],
        group['RPFPRank']
    ))

# Create indexes for better query performance
cursor.execute('CREATE INDEX IF NOT EXISTS idx_fights_date ON Fights(Date)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_fights_winner ON Fights(Winner)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_fights_weightclass ON Fights(WeightClass)')

# Commit changes and close connection
conn.commit()
conn.close()

print('Database tables have been created successfully with fighter names as keys.')