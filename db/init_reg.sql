CREATE TABLE Teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    logo_path VARCHAR(255),
    group_name VARCHAR(10), -- Group A, B, etc.
    
    cap_name VARCHAR(50) NOT NULL,
    cap_surname VARCHAR(50) NOT NULL,
    cap_email VARCHAR(100) UNIQUE NOT NULL,
    cap_phone VARCHAR(20) UNIQUE,
    
    payment_status INTEGER DEFAULT 0, -- 0 = waiting, 1 = accepted, 2 = refund
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    jersey_number INTEGER,
    
    FOREIGN KEY (team_id) REFERENCES Teams(id) ON DELETE CASCADE
);

CREATE TABLE Matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_a_id INTEGER NOT NULL,
    team_b_id INTEGER NOT NULL,
    winner_id INTEGER, -- Reference to the winner team
    
    status INTEGER DEFAULT 0, -- 0 scheduled, 1 live, 2 finished, 3 canceled
    match_type VARCHAR(20) NOT NULL, -- group, play-off, final
    queue_number INTEGER, -- Round number or order
    location VARCHAR(50), -- Table/Court/Field
    
    scheduled_at TIMESTAMP,
    score_a INTEGER DEFAULT 0,
    score_b INTEGER DEFAULT 0,
    current_points_a INTEGER DEFAULT 0, -- Points in the current set
    current_points_b INTEGER DEFAULT 0,
    
    detailed_results JSON, -- Store play-by-play here: "who scored", "minutes"
    
    FOREIGN KEY (team_a_id) REFERENCES Teams(id),
    FOREIGN KEY (team_b_id) REFERENCES Teams(id),
    FOREIGN KEY (winner_id) REFERENCES Teams(id)
);
CREATE TABLE Match_Stats_Events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    set_number INTEGER NOT NULL, -- 1, 2, 3, 4, 5
    
    -- Action type (matches the columns in your stat sheet)
    -- 'SA', 'A', 'SE' (Serve)
    -- 'ATT', 'K', 'E' (Attack)
    -- 'R', 'RE' (Reception)
    -- 'BS', 'BA', 'BE' (Block)
    -- 'BHA', 'AST', 'BHE' (Set/Assist)
    -- 'D', 'DE' (Defense/Digs)
    action_type VARCHAR(5) NOT NULL,
    
    -- Rally number for ordering / chronology
    rally_number INTEGER, 
    
    FOREIGN KEY (match_id) REFERENCES Matches(id),
    FOREIGN KEY (player_id) REFERENCES Players(id),
    FOREIGN KEY (team_id) REFERENCES Teams(id)
);
CREATE TABLE Match_Sets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL,
    set_number INTEGER NOT NULL, -- 1, 2, 3, 4, 5
    score_team_a INTEGER DEFAULT 0,
    score_team_b INTEGER DEFAULT 0,
    FOREIGN KEY (match_id) REFERENCES Matches(id)
);