# MySQL Universe Database
# Data Engineering CourseWork

import mysql.connector
from mysql.connector import Error
import csv

def create_mysql_connection(host_name, user_name, user_password):
    """
    Creates and returns a MySQL connection.
    """
    try:
        connection = mysql.connector.connect(
            host='',
            user='',
            password=''  # Add your MySQL password here
        )
        if connection.is_connected():
            print("Connected to MySQL")
            return connection
    except Error as e:
        print(f"Error: '{e}'")
        return None
    
def create_database(connection, db_name):
    """
    Creates a database if it doesn't already exist.
    """
    try:
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        print(f"Database '{db_name}' created or already exists.")
        cursor.close()
    except Error as e:
        print(f"Error: '{e}'")
        
        
def create_tables(connection, db_name):
    """
    Creating DB tables
    """
    try:
        connection.database = db_name
        cursor = connection.cursor()
       
        # Creating Galaxy table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Galaxy (
            gid VARCHAR(50) PRIMARY KEY,
            name TEXT,
            morphology TEXT,
            size FLOAT,
            mass FLOAT,
            age FLOAT
        );
        """)
        
        # Creating Solar_System table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Solar_System (
        	ssid VARCHAR(50) PRIMARY KEY,
            gid VARCHAR(50) NOT NULL,
            name TEXT,
            size FLOAT,
            age FLOAT,
            FOREIGN KEY (gid) REFERENCES Galaxy(gid)
                ON DELETE CASCADE
        );
        """)
       
        # Creating Star table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Star(
        	sid VARCHAR(50) PRIMARY KEY,
            gid VARCHAR(50),
            ssid VARCHAR(50),
            name TEXT,
            age FLOAT,
            radius FLOAT,
            mass FLOAT,
            temperature FLOAT,
            luminosity DOUBLE,
            gravity FLOAT,
            state ENUM('Main Sequence', 'Supergiant', 'Red Giant', 'White Dwarf', 'Neutron Star', 'Black Hole') NOT NULL,
            FOREIGN KEY (ssid) REFERENCES Solar_System(ssid)
                ON DELETE SET NULL,
            FOREIGN KEY (gid) REFERENCES Galaxy(gid) 
                ON DELETE SET NULL   
        );
        """)
        
        # Creating Black_Hole table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Black_Hole (
        	sid VARCHAR(50) PRIMARY KEY,
            electric_charge FLOAT,
            angular_momentum FLOAT,
            FOREIGN KEY (sid) REFERENCES Star(sid)
                ON DELETE CASCADE
        );
        """)
        
        # Creating Planet table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Planet (
        	pid VARCHAR(50) PRIMARY KEY,
            ssid VARCHAR(50),
            gid VARCHAR(50) NOT NULL,
            name TEXT,
            atmosphere TEXT,
            habitable TINYINT(1),
            type TEXT,
            FOREIGN KEY (ssid) REFERENCES Solar_System(ssid)
                ON DELETE SET NULL,
            FOREIGN KEY (gid) REFERENCES Galaxy(gid)
                ON DELETE CASCADE
        );
        """)
       
        # Creating Moon table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Moon (
        	pid VARCHAR(50),
            name VARCHAR(255) NOT NULL,
            radius FLOAT,
            tidal_locked TINYINT(1),
            albedo FLOAT,
            gravity FLOAT,
            PRIMARY KEY (pid, name),
            FOREIGN KEY (pid) REFERENCES Planet(pid)
                ON DELETE CASCADE
        );
        """)
       
        print("Tables Galaxy, Star, Solar_System, Black_Hole, Planet, Moon, and type 'stellar_state' created or already exist.")
        cursor.close()
    except Error as e:
        print(f"Error: '{e}'")

def populate_table_csv(connection, csv_file_path, table_name):
    """
    Populates a specified table from a CSV file.
    """
    try:
        cursor = connection.cursor()
        with open(csv_file_path, mode='r') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)  # Skip header row
           
            # Define insert query based on table
            if table_name == 'Galaxy':
                insert_query = """
                INSERT INTO Galaxy (gid,name,morphology,size,mass,age)
                VALUES (%s,%s,%s,%s,%s,%s)
                """
            elif table_name == 'Star':
                insert_query = """
                INSERT INTO Star (sid,gid,ssid,name,age,radius,mass,temperature,luminosity,gravity,state)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """
            elif table_name == 'Solar_System':
                insert_query = """
                INSERT INTO Solar_System (ssid,gid,name,size,age)
                VALUES (%s,%s,%s,%s,%s)
                """
            elif table_name == 'Black_Hole':
                insert_query = """
                INSERT INTO Black_Hole (sid, electric_charge, angular_momentum)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    electric_charge = VALUES(electric_charge),
                    angular_momentum = VALUES(angular_momentum)
                """                         # <------- Needs to update instead of insert due to ISA relationship.
            elif table_name == 'Planet':
                insert_query = """
                INSERT INTO Planet (pid,ssid,gid,name,atmosphere,habitable,type)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                """
            elif table_name == 'Moon':
                insert_query = """
                INSERT INTO Moon (pid,name,radius,tidal_locked,albedo,gravity)
                VALUES (%s,%s,%s,%s,%s,%s)
                """
                
            else:
                raise ValueError(f"Unknown table name: {table_name}")
                            
            # Insert each row from CSV into the table
            rows = []
            for row in csv_reader:
                if not any(row):  # Skip empty rows
                    continue
                row = [None if val == "NULL" else val for val in row]
                rows.append(tuple(row))

            for row in rows:
                cursor.execute(insert_query, row)

            connection.commit()
        print(f"Data from '{csv_file_path}' inserted successfully into '{table_name}' table.")
        cursor.close()
    except Error as e:
        print(f"Error: '{table_name}' '{e}'")

########################################----------DEBUG-----------#############################################

def drop_all_tables(connection):
      try:
          cursor = connection.cursor()
          # Drop in reverse order of dependencies
          cursor.execute("DROP TABLE IF EXISTS Black_Hole")
          cursor.execute("DROP TABLE IF EXISTS Moon")
          cursor.execute("DROP TABLE IF EXISTS Planet")
          cursor.execute("DROP TABLE IF EXISTS Star")
          cursor.execute("DROP TABLE IF EXISTS Solar_System")
          cursor.execute("DROP TABLE IF EXISTS Galaxy")
          connection.commit()
          print("All tables dropped.")
          cursor.close()
      except Error as e:
          print(f"Error: '{e}'")

########################################----------ENDOFDEBUG-----------#############################################


##############################----------TRIGGERS AND VALIDATIONS-----------#########################################

def cleanup_invalid_solar_systems(connection):
    """
    Deletes solar systems that don't have at least one star AND one planet.
    Prints detailed messages for each deletion.
    """
    cursor = connection.cursor()
    
    # Find solar systems without required stars or planets
    cursor.execute("""
        SELECT ss.ssid, ss.name,
               COUNT(DISTINCT s.sid) as star_count,
               COUNT(DISTINCT p.pid) as planet_count
        FROM Solar_System ss
        LEFT JOIN Star s ON ss.ssid = s.ssid
        LEFT JOIN Planet p ON ss.ssid = p.ssid
        GROUP BY ss.ssid, ss.name
        HAVING star_count = 0 OR planet_count = 0
    """)
    
    invalid_systems = cursor.fetchall()
    
    if invalid_systems:
        print(f"\n[!] Found {len(invalid_systems)} invalid solar system(s):\n")
        
        for ssid, name, star_count, planet_count in invalid_systems:
            # Determine what's missing
            if star_count == 0:
                print(f"Solar System {name} ({ssid} has no stars.)")
            if planet_count == 0:
                print(f"Solar System {name} ({ssid} has no planets.)")
                
            # Delete the solar system
            cursor.execute("DELETE FROM Solar_System WHERE ssid = %s", (ssid,))
            print(f"Solar system deleted. Solar systems must have stars and planets.\n")
        
        connection.commit()
        print(f"[OK] Cleaned up {len(invalid_systems)} invalid solar system(s)\n")
    else:
        print("[OK] All solar systems are valid (have both stars and planets)\n")
    
    cursor.close()
    
def cascade_solarSystem(connection):
    """
    Creates triggers to auto-delete solar systems when they become empty.
    - Deleting the LAST star → solar system deleted
    - Deleting the LAST planet → solar system deleted
    - Deleting any non-last star/planet → solar system remains
    """
    try:
        cursor = connection.cursor()
        
        print("Creating triggers for solar system auto-deletion...")
        
        cursor.execute("DROP TRIGGER IF EXISTS auto_delete_empty_solar_system_on_star_delete")
        cursor.execute("DROP TRIGGER IF EXISTS auto_delete_empty_solar_system_on_planet_delete")
        
        # Trigger 1: Check after ANY star deletion - only delete solar system if it was the LAST star
        cursor.execute("""
        CREATE TRIGGER auto_delete_empty_solar_system_on_star_delete
        AFTER DELETE ON Star
        FOR EACH ROW
        BEGIN
            DECLARE star_count INT;
            DECLARE planet_count INT;
            
            IF OLD.ssid IS NOT NULL THEN
                -- Count REMAINING stars (after this deletion)
                SELECT COUNT(*) INTO star_count FROM Star WHERE ssid = OLD.ssid;
                -- Count REMAINING planets
                SELECT COUNT(*) INTO planet_count FROM Planet WHERE ssid = OLD.ssid;
                
                -- Only delete solar system if NO stars left OR NO planets left
                IF star_count = 0 OR planet_count = 0 THEN
                    DELETE FROM Solar_System WHERE ssid = OLD.ssid;
                END IF;
            END IF;
        END
        """)
        print("[+] Created trigger: auto_delete_empty_solar_system_on_star_delete")
        
        # Trigger 2: Check after ANY planet deletion - only delete solar system if it was the LAST planet
        cursor.execute("""
        CREATE TRIGGER auto_delete_empty_solar_system_on_planet_delete
        AFTER DELETE ON Planet
        FOR EACH ROW
        BEGIN
            DECLARE star_count INT;
            DECLARE planet_count INT;
            
            IF OLD.ssid IS NOT NULL THEN
                -- Count REMAINING stars
                SELECT COUNT(*) INTO star_count FROM Star WHERE ssid = OLD.ssid;
                -- Count REMAINING planets (after this deletion)
                SELECT COUNT(*) INTO planet_count FROM Planet WHERE ssid = OLD.ssid;
                
                -- Only delete solar system if NO planets left OR NO stars left
                IF star_count = 0 OR planet_count = 0 THEN
                    DELETE FROM Solar_System WHERE ssid = OLD.ssid;
                END IF;
            END IF;
        END
        """)
        print("[+] Created trigger: auto_delete_empty_solar_system_on_planet_delete")
        
        print("All triggers created successfully.\n")
        cursor.close()
    except Error as e:
        print(f"Error creating triggers: '{e}'")
        
def blackHole_ISA(connection):
    """
    Creates triggers to enforce Black Hole ISA relationship.
    Automatically creates/deletes Black_Hole entries when Star state changes.
    """
    try:
        cursor = connection.cursor()
        
        print("Creating Black Hole ISA triggers...")
        
        # Drop existing triggers
        cursor.execute("DROP TRIGGER IF EXISTS enforce_black_hole_isa_on_insert")
        cursor.execute("DROP TRIGGER IF EXISTS enforce_black_hole_isa_on_update")
        
        # Trigger 1: When inserting a Star with state='Black Hole', auto create Black_Hole entry
        cursor.execute("""
        CREATE TRIGGER enforce_black_hole_isa_on_insert
        AFTER INSERT ON Star
        FOR EACH ROW
        BEGIN
            IF NEW.state = 'Black Hole' THEN
                INSERT INTO Black_Hole (sid, electric_charge, angular_momentum)
                VALUES (NEW.sid, 0.0, 0.0)
                ON DUPLICATE KEY UPDATE sid = sid;
            END IF;
        END
        """)
        print("[+] Created trigger: enforce_black_hole_isa_on_insert")
        
        # Trigger 2: When updating a Star's state, manage Black_Hole entry accordingly
        cursor.execute("""
        CREATE TRIGGER enforce_black_hole_isa_on_update
        AFTER UPDATE ON Star
        FOR EACH ROW
        BEGIN
            -- If state changed TO 'Black Hole', create Black_Hole entry
            IF NEW.state = 'Black Hole' AND OLD.state != 'Black Hole' THEN
                INSERT INTO Black_Hole (sid, electric_charge, angular_momentum)
                VALUES (NEW.sid, 0.0, 0.0)
                ON DUPLICATE KEY UPDATE sid = sid;
            END IF;
            
            -- If state changed FROM 'Black Hole' to something else, remove Black_Hole entry
            IF OLD.state = 'Black Hole' AND NEW.state != 'Black Hole' THEN
                DELETE FROM Black_Hole WHERE sid = OLD.sid;
            END IF;
        END
        """)
        print("[+] Created trigger: enforce_black_hole_isa_on_update")
        
        print("Black Hole ISA triggers created successfully.\n")
        cursor.close()
    except Error as e:
        print(f"Error creating Black Hole ISA triggers: '{e}'")

#################################################################################################################

###################################--------Plotting Queries--------##############################################

def create_query_dashboard(connection):
    """
    Creates a comprehensive dashboard showing all 4 query results in one view.
    """
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go
    
    cursor = connection.cursor()
    
    print("Creating comprehensive dashboard...")
    
    # ==================== QUERY 1: MULTIPLE STAR SYSTEMS ====================
    cursor.execute("""
        SELECT Solar_System.name, COUNT(Star.sid) AS star_count
        FROM Solar_System
        JOIN Star ON Solar_System.ssid = Star.ssid
        GROUP BY Solar_System.ssid
        HAVING COUNT(Star.sid) >= 2
        ORDER BY star_count DESC
    """)
    multi_star_results = cursor.fetchall()
    
    # ==================== QUERY 2: EXOPLANETS BY GALAXY ====================
    cursor.execute("""
        SELECT Galaxy.name, COUNT(Planet.pid) AS planet_count
        FROM Planet
        JOIN Galaxy ON Planet.gid = Galaxy.gid
        WHERE Planet.ssid IS NULL
        GROUP BY Galaxy.gid, Galaxy.name
        ORDER BY planet_count DESC
    """)
    exoplanet_results = cursor.fetchall()
    
    # ==================== QUERY 3: ROGUE STARS BY STATE ====================
    cursor.execute("""
        SELECT state, COUNT(*) AS count
        FROM Star
        WHERE gid IS NULL AND state != 'Black Hole'
        GROUP BY state
        ORDER BY count DESC
    """)
    rogue_star_results = cursor.fetchall()
    
    # ==================== QUERY 4: SUPERMASSIVE BLACK HOLES ====================
    cursor.execute("""
        SELECT Star.name, Star.mass
        FROM Star
        JOIN Black_Hole ON Star.sid = Black_Hole.sid
        WHERE Star.state = 'Black Hole' AND Star.mass >= 1000000
        ORDER BY Star.mass DESC
    """)
    supermassive_results = cursor.fetchall()
    
    cursor.close()
    
    # ==================== CREATE 2x2 SUBPLOT GRID ====================
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Query 1: Multiple Star Systems",
            "Query 2: Exoplanets by Galaxy",
            "Query 3: Rogue Stars by Stellar State",
            "Query 4: Supermassive Black Holes (Mass ≥ 1M M☉)"
        ),
        specs=[
            [{"type": "bar"}, {"type": "pie"}],
            [{"type": "bar"}, {"type": "bar"}]
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )
    
    # ==================== PLOT 1: MULTIPLE STAR SYSTEMS ====================
    if multi_star_results:
        system_names = [r[0] for r in multi_star_results]
        star_counts = [r[1] for r in multi_star_results]
        
        fig.add_trace(
            go.Bar(
                x=system_names,
                y=star_counts,
                text=star_counts,
                textposition='auto',
                marker=dict(
                    color=star_counts,
                    colorscale='Blues',
                    showscale=False
                ),
                name="Stars",
                hovertemplate='<b>%{x}</b><br>Stars: %{y}<extra></extra>'
            ),
            row=1, col=1
        )
        fig.update_xaxes(title_text="Solar System", row=1, col=1)
        fig.update_yaxes(title_text="Number of Stars", row=1, col=1)
    else:
        # Show "No data" message
        fig.add_annotation(
            text="No multiple star systems found",
            xref="x domain", yref="y domain",
            x=0.5, y=0.5,
            showarrow=False,
            row=1, col=1
        )
    
    # ==================== PLOT 2: EXOPLANETS (PIE CHART) ====================
    if exoplanet_results:
        galaxy_names = [r[0] for r in exoplanet_results]
        exoplanet_counts = [r[1] for r in exoplanet_results]
        
        fig.add_trace(
            go.Pie(
                labels=galaxy_names,
                values=exoplanet_counts,
                hole=0.3,  # Donut chart
                marker=dict(colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']),
                textinfo='label+percent+value',
                hovertemplate='<b>%{label}</b><br>Exoplanets: %{value}<br>%{percent}<extra></extra>'
            ),
            row=1, col=2
        )
    else:
        fig.add_annotation(
            text="No exoplanets found",
            xref="x2 domain", yref="y2 domain",
            x=0.5, y=0.5,
            showarrow=False,
            row=1, col=2
        )
    
    # ==================== PLOT 3: ROGUE STARS BY STATE ====================
    if rogue_star_results:
        states = [r[0] for r in rogue_star_results]
        state_counts = [r[1] for r in rogue_star_results]
        
        fig.add_trace(
            go.Bar(
                x=states,
                y=state_counts,
                text=state_counts,
                textposition='auto',
                marker=dict(
                    color=state_counts,
                    colorscale='Greens',
                    showscale=False
                ),
                name="Rogue Stars",
                hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>'
            ),
            row=2, col=1
        )
        fig.update_xaxes(title_text="Stellar State", row=2, col=1)
        fig.update_yaxes(title_text="Count", row=2, col=1)
    else:
        fig.add_annotation(
            text="No rogue stars found",
            xref="x3 domain", yref="y3 domain",
            x=0.5, y=0.5,
            showarrow=False,
            row=2, col=1
        )
    
    # ==================== PLOT 4: SUPERMASSIVE BLACK HOLES ====================
    if supermassive_results:
        bh_names = [r[0] for r in supermassive_results]
        bh_masses = [r[1] for r in supermassive_results]
        
        # Convert to millions of solar masses for display
        bh_masses_millions = [m / 1e6 for m in bh_masses]
        
        fig.add_trace(
            go.Bar(
                y=bh_names,  # Horizontal bars (swap x and y)
                x=bh_masses_millions,
                orientation='h',
                text=[f"{m:.1f}M" for m in bh_masses_millions],
                textposition='auto',
                marker=dict(
                    color=bh_masses,
                    colorscale='Reds',
                    showscale=False
                ),
                name="Mass",
                hovertemplate='<b>%{y}</b><br>Mass: %{x:.2f} million M☉<extra></extra>'
            ),
            row=2, col=2
        )
        fig.update_xaxes(title_text="Mass (Million M☉)", row=2, col=2)
        fig.update_yaxes(title_text="Black Hole", row=2, col=2)
    else:
        fig.add_annotation(
            text="No supermassive black holes found",
            xref="x4 domain", yref="y4 domain",
            x=0.5, y=0.5,
            showarrow=False,
            row=2, col=2
        )
    
    # ==================== LAYOUT ====================
    fig.update_layout(
        title={
            'text': "Astronomy Database - Query Results Dashboard",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'color': 'white'}
        },
        template="plotly_dark",
        height=1000,
        showlegend=False,
        font=dict(size=12)
    )
    
    # Save and display
    fig.write_html("query_results_dashboard.html")
    print("✓ Dashboard saved: query_results_dashboard.html")
    
    fig.show()
    
    return fig

###############################--------End of Plotting Queries--------###########################################

def main():
    # MySQL connection details
    host_name = ""
    user_name = ""
    user_password = ""  
    db_name = "Universe_DB"

    # Create MySQL connection
    connection = create_mysql_connection(host_name, user_name, user_password)
   
    if connection:
        try:
            #Create the database
            create_database(connection, db_name)
            connection.database = db_name
           #DEBUG----------------------------------------
            drop_all_tables(connection)
           #---------------------------------------------
           
            #Create the tables in the database
            create_tables(connection, db_name)   
            
            print("\n--- Populating tables ---\n")
        
            # 1. Galaxy (no dependencies)
            populate_table_csv(connection, "Galaxy.csv", "Galaxy")
            # 2. Solar_System (depends on Galaxy)
            populate_table_csv(connection, "Solar_System.csv", "Solar_System")   # <--- Needs to be before star and planet due to FK constraint.
            # 3. Star (depends on Galaxy and Solar_System)
            populate_table_csv(connection, "Star.csv", "Star")
            # 4. Planet (depends on Solar_System)
            populate_table_csv(connection, "Planet.csv", "Planet")
            # 5. Moon (depends on Planet)
            populate_table_csv(connection, "Moon.csv", "Moon")                  # <--- Needs to be after planet due to dependency.
            # 6. Black_Hole (depends on Star - ISA relationship)
            populate_table_csv(connection, "Black_Hole.csv", "Black_Hole")      # <--- Needs to be after star due to ISA relationship.
            
            connection.commit()
            print("\n--- All data inserted ---\n")
            
            print("+" + "-" * 78 + "+")
            print("|  UNITS:                                                                      |")
            print("|    - Age: years                                                              |")
            print("|    - Distance/Size: ly (light years), AU (astronomical units), km            |")
            print("|    - Mass: solar masses                                                      |")
            print("|    - Temperature: K (Kelvin)                                                 |")
            print("|    - Luminosity: solar luminosities                                          |")
            print("|    - Gravity: m/s^2 (meters per second squared)                              |")
            print("|    - Electric Charge: C (Coulombs)                                           |")
            print("|    - Albedo: 0-1 (dimensionless)                                             |")
            print("|    - Angular Momentum: 0-1 a                                                 |")
            print("+" + "-" * 78 + "+")
            print()
            
            #Executing queries:
        
            # Validate and cleanup invalid solar systems
            print("--- Validating solar systems ---\n")
            cleanup_invalid_solar_systems(connection)
            
            # Ensure Solar System cascade if last star or planet deleted
            print("--- Creating triggers for Solar System cascade ---\n")
            cascade_solarSystem(connection)
            
            # Creating Black Hole ISA relationship, turning a Star into a Black Hole through its state
            print("--- Creating triggers for Black Hole ISA relationship ---\n")
            blackHole_ISA(connection)
           
           # CREATE VISUAL DASHBOARD
            print("=" * 80)
            print("CREATING VISUAL DASHBOARD")
            print("=" * 80)
            print()
            
            create_query_dashboard(connection)
            
            print()
            print("=" * 80)
            print("✓ ALL QUERIES COMPLETED AND VISUALIZED!")
            print("  Open 'query_results_dashboard.html' in your browser to see the dashboard")
            print("=" * 80)
            print()
           
        except Error as e:
            print(f"\n❌ DATABASE ERROR: {e}")
            connection.rollback() 
        finally:
            connection.close()
            print("MySQL connection closed.")
    else:
        print("Failed to connect to MySQL")


if __name__ == "__main__":
    main()
    


