from flask import Flask, render_template, request, redirect, url_for
import csv
import hashlib
import sympy
import mysql.connector
from collections import Counter

app = Flask(__name__)

class VotingSystem:
    def __init__(self):
        self.candidates = {}
        self.voters = {}
        self.votes = {}
        self.results = {}
        self.db_connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="1234",
            database="voting_system"
        )
        self.db_cursor = self.db_connection.cursor(dictionary=True)

    def candidate_vote_count(self, decrypted_votes):
        try:
            # Execute the query to select candidate names from the 'candidates' table
            self.db_cursor.execute("SELECT candidate_name FROM candidates")

            # Fetch all rows from the result set
            candidate_rows = self.db_cursor.fetchall()

            if not candidate_rows:
                # No candidates found, return an appropriate value (e.g., empty dictionary)
                return {}

            # Extract candidate names from the rows
            candidate_names_from_db = [candidate['candidate_name'] for candidate in candidate_rows]
            candidate_names_from_db.append('NOTA')
            # Use Counter to count occurrences of each hashed candidate name in decrypted_votes
            vote_counts = Counter(decrypted_votes)
            candidate_vote_counts = {candidate_name: vote_counts.get(int.from_bytes(hashlib.sha256(candidate_name.encode('utf-8')).digest(), byteorder='big'), 0) for candidate_name in candidate_names_from_db}
            
            return candidate_vote_counts

        except Exception as e:
            print(f"An error occurred while extracting candidate names from the database: {e}")
            # Return an appropriate value (e.g., empty dictionary) in case of an exception
            return {}


    def load_and_decode_votes(self):
        decrypted_votes = []
        try:
            # Connect to the MySQL database
            with mysql.connector.connect(
                host="localhost",
                user="root",
                password="1234",
                database="voting_system"
            ) as connection, connection.cursor(dictionary=True) as cursor:
                # Execute the query to select encrypted votes and private keys from the 'votes' table
                cursor.execute("SELECT encrypted_vote, private_key FROM votes")

                # Fetch all rows from the result set
                votes_from_db = cursor.fetchall()

                # Loop through each row and decode the votes
                for vote_data in votes_from_db:
                    encrypted_vote = int(vote_data['encrypted_vote'])
                    private_key_str = vote_data['private_key'][1:-1]
                    private_key = tuple(map(int, private_key_str.split(',')))

                    # Use the VotingSystem's rsa_decode method (you may need to adjust this based on your actual method)
                    decrypted_vote = voting_system.rsa_decode(encrypted_vote, private_key[0], private_key[1])

                    # Append the decrypted vote to the list
                    decrypted_votes.append(decrypted_vote)

        except Exception as e:
            print(f"An error occurred while loading and decoding votes: {e}")

        return decrypted_votes

    def load_candidates_from_database(self):
        try:
            # Connect to your MySQL database (replace with your database details)
            connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password='1234',
                database='voting_system'
            )

            # Create a cursor object to interact with the database
            cursor = connection.cursor(dictionary=True)

            # Execute the query to fetch candidate_id and candidate_name columns
            cursor.execute('SELECT candidate_id, candidate_name FROM candidates')

            # Fetch all rows as a list of dictionaries
            candidates = cursor.fetchall()

            # Update the candidates attribute in VotingSystem
            self.candidates = candidates

        except Exception as e:
            print(f"Error loading candidates: {e}")

        finally:
            # Close the cursor and connection
            cursor.close()
            connection.close()
                
    def save_vote_to_database(self, encrypted_vote, private_key):
        try:
            # Connect to the MySQL database
            connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="1234",
                database="voting_system"
            )

            # Create a cursor object to execute SQL queries
            cursor = connection.cursor()

            # Convert the tuple to a string or another appropriate type
            encrypted_vote_str = str(encrypted_vote)
            private_key_str = str(private_key)

            # Execute the query to insert the vote into the 'votes' table
            query = "INSERT INTO votes (encrypted_vote, private_key) VALUES (%s, %s)"
            values = (encrypted_vote_str, private_key_str)
            cursor.execute(query, values)

            # Commit the changes and close the cursor and connection
            connection.commit()
            cursor.close()
            connection.close()

            print("Vote has been successfully saved to the database.")

        except Exception as e:
            print(f"An error occurred while saving vote to the database: {e}")

    

    def save_decrypted_votes_to_csv(self, output_filename):
        with open(output_filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['decrypted_vote'])
            for voter_id, vote_data in self.votes.items():
                private_key = self.voters[voter_id]['private_key']
                encrypted_vote = vote_data['encrypted_vote']
                decrypted_vote = self.rsa_decode(encrypted_vote, private_key[0], private_key[1])
                writer.writerow([decrypted_vote])
        print(f"Decrypted votes saved to {output_filename}")

    def load_voters_from_database(self):
        try:
            # Execute the query to select all voters from the 'voters' table
            query = "SELECT * FROM voters"
            self.db_cursor.execute(query)

            # Fetch all rows from the result set
            voters_from_db = self.db_cursor.fetchall()

            # Populate the voters dictionary with data from the database
            for voter in voters_from_db:
                voter_id = voter['voter_id']
                # Extracting x and y values from the string and converting them to integers
                public_key_str = voter['public_key'][1:-1]  # Remove parentheses
                public_key = tuple(map(int, public_key_str.split(',')))

                private_key_str = voter['private_key'][1:-1]  # Remove parentheses
                private_key = tuple(map(int, private_key_str.split(',')))

                has_voted = bool(voter['has_voted'])

                self.voters[voter_id] = {
                    'public_key': public_key,
                    'private_key': private_key,
                    'has_voted': has_voted,
                    'name': voter['name']
                }

        except Exception as e:
            print(f"An error occurred while loading voter data from the database: {e}")
            
    def is_valid_voter(self, voter_id):
        try:
            # Execute the query to check if the voter ID exists
            query = "SELECT * FROM voters WHERE voter_id = %s"
            self.db_cursor.execute(query, (voter_id,))
            result = self.db_cursor.fetchone()

            # If result is not None, the voter ID is valid
            return result is not None

        except Exception as e:
            print(f"An error occurred while checking voter validity: {e}")
            return False
    def is_valid_candidate(self, candidate_id):
        try:
            # Execute the query to check if the candidate ID exists
            query = "SELECT * FROM candidates WHERE candidate_id = %s"
            self.db_cursor.execute(query, (candidate_id,))
            result = self.db_cursor.fetchone()

            # If result is not None, the candidate ID is valid
            return result is not None

        except Exception as e:
            print(f"An error occurred while checking candidate validity: {e}")
            return False

    def register_candidate(self, candidate_id, candidate_name, candidate_age):
        # Your existing candidate registration logic here
        if candidate_age >= 30 and candidate_age <= 60:
            if not self.is_valid_candidate(candidate_id):
                # Insert the candidate into the 'candidates' table
                query = "INSERT INTO candidates (candidate_id, candidate_name, candidate_age) VALUES (%s, %s, %s)"
                values = (candidate_id, candidate_name, candidate_age)
                self.db_cursor.execute(query, values)
                self.db_connection.commit()

                print(f"Candidate {candidate_id} ({candidate_name}) has been registered.")
                return f"Candidate {candidate_id} registration submitted successfully."
            else:
                return f"Candidate {candidate_id} is already registered."
        else:
            return f"Candidate {candidate_id} does not meet the age requirement (30-60 years)."

    def save_candidates_to_csv(self, filename):
        try:
            # Execute the query to select all candidates from the 'candidates' table
            query = "SELECT * FROM candidates"
            self.db_cursor.execute(query)

            # Fetch all rows from the result set
            candidates_from_db = self.db_cursor.fetchall()

            # Write all candidates to the CSV file
            with open(filename, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['candidate_id', 'candidate_name', 'candidate_age'])
                for candidate in candidates_from_db:
                    writer.writerow([candidate['candidate_id'], candidate['candidate_name'], candidate['candidate_age']])

        except Exception as e:
            print(f"An error occurred while saving candidates to the CSV file: {e}")

    def register_voter(self, voter_id, voter_name):
        # Your existing voter registration logic here
        if not self.is_valid_voter(voter_id):
            keypair = self.generate_rsa_keypair(1024)
            self.voters[voter_id] = {
                'public_key': keypair[0],
                'private_key': keypair[1],
                'has_voted': False,
                'name': voter_name
            }

            # Store voter information in the MySQL database
            query = "INSERT INTO voters (voter_id, name, public_key, private_key, has_voted) VALUES (%s, %s, %s, %s, %s)"
            values = (voter_id, voter_name, str(keypair[0]), str(keypair[1]), False)
            self.db_cursor.execute(query, values)
            self.db_connection.commit()

            print(f"Voter {voter_id} ({voter_name}) has been registered.")
            return f"Voter {voter_id} registration submitted successfully."
        else:
            return f"Voter {voter_id} is already registered."
    def cast_vote(self, candidate_id, public_key):
        if candidate_id == 0:  # Vote for NOTA
            candidate_name = "NOTA"
        elif self.is_valid_candidate(candidate_id):
            # Execute the query to select the candidate name from the 'candidates' table
            query = "SELECT candidate_name FROM candidates WHERE candidate_id = %s"
            self.db_cursor.execute(query, (candidate_id,))
            result = self.db_cursor.fetchone()

            if result:
                candidate_name = result['candidate_name']
            else:
                print(f"Candidate ID {candidate_id} not found in candidates table.")
                return None
        else:
            print(f"Invalid candidate ID: {candidate_id}.")
            return None  # or handle the error appropriately

        candidate_bytes = candidate_name.encode('utf-8')
        hashed_candidate = hashlib.sha256(candidate_bytes).digest()
        vote = int.from_bytes(hashed_candidate, byteorder='big')
        encrypted_vote = self.rsa_encode(vote, public_key[0], public_key[1])

        print(f"Vote for Candidate ID {candidate_id} ({candidate_name}): Encrypted Vote - {encrypted_vote}")

        return encrypted_vote
    
    def generate_rsa_keypair(self, bits):
        p = sympy.randprime(2 ** (bits // 2), 2 ** (bits // 2 + 1))
        q = sympy.randprime(2 ** (bits // 2), 2 ** (bits // 2 + 1))
        n = p * q
        phi = (p - 1) * (q - 1)
        e = 65537
        d = sympy.mod_inverse(e, phi)
        return ((e, n), (d, n))

    def rsa_encode(self, message, e, n):
        return pow(message, e, n)

    def rsa_decode(self, ciphertext, d, n):
        return pow(ciphertext, d, n)
    def mark_voter_as_voted(self, voter_id):
        try:
            # Execute the query to update the 'has_voted' field for the voter
            query = "UPDATE voters SET has_voted = %s WHERE voter_id = %s"
            values = (True, voter_id)
            self.db_cursor.execute(query, values)
            self.db_connection.commit()
            print(f"Voter {voter_id} has been marked as voted in the database.")
        except Exception as e:
            print(f"An error occurred while updating voter status in the database: {e}")

    def vote(self, voter_id, candidate_id):
        
        if voter_id in self.voters:
            # Ensure the voters dictionary is updated with the latest data from the database
            self.load_voters_from_database()

            if not self.voters[voter_id]['has_voted']:
                public_key = self.voters[voter_id]['public_key']

                # Check if the voter ID is valid
                if self.is_valid_voter(voter_id):
                    # If the candidate ID is NOTA (0), proceed without further validation
                    if candidate_id == 0:
                        encrypted_vote = self.cast_vote(candidate_id, public_key)
                        private_key = self.voters[voter_id]['private_key']
                        self.save_vote_to_database(encrypted_vote, private_key)
                        self.mark_voter_as_voted(voter_id)
                        #print(f"Voter {voter_id} has voted for NOTA.")
                        return f"Vote submitted successfully for Voter {voter_id} to NOTA."
                    else:
                        # Check if the candidate ID is valid
                        if self.is_valid_candidate(candidate_id):
                            # Continue with the rest of the logic for casting the vote
                            encrypted_vote = self.cast_vote(candidate_id, public_key)
                            private_key = self.voters[voter_id]['private_key']

                            # Insert the vote into the 'votes' table
                            self.save_vote_to_database(encrypted_vote, private_key)

                            self.mark_voter_as_voted(voter_id)
                            #print(f"Voter {voter_id} has voted for Candidate {candidate_id}.")
                            return f"Vote submitted successfully for Voter {voter_id} to Candidate {candidate_id}."
                        else:
                            return f"Invalid candidate ID: {candidate_id}. Please choose a valid candidate."
                else:
                    return f"Invalid voter ID: {voter_id}. Please enter a valid voter ID."
            else:
                return f"Voter {voter_id} has already voted."


    

# Create an instance of the VotingSystem
voting_system = VotingSystem()
#decrypted_votes=voting_system.load_and_decode_votes()
#print(decrypted_votes)
#candidate_count=voting_system.candidate_vote_count(decrypted_votes)
#print(candidate_count)
@app.route('/')
def candidate_registration():
    return render_template('candidate_registration.html')
@app.route('/index')
def index():
    # Retrieve candidate information from VotingSystem
    voting_system.load_voters_from_database()
    voting_system.load_candidates_from_database()
    candidates = voting_system.candidates
    print("Candidates:", candidates)
    return render_template('index.html', candidates=candidates)
@app.route('/register_candidate', methods=['POST'])
def register_candidate():
    # Handle candidate registration here
    candidate_id = int(request.form['candidate_id'])
    candidate_name = request.form['candidate_name']
    candidate_age = int(request.form['candidate_age'])
    
    message = voting_system.register_candidate(candidate_id, candidate_name, candidate_age)

    # Retrieve candidate information from VotingSystem (optional)
    voting_system.load_voters_from_database()
    candidates = voting_system.candidates

    # Render the candidate_registration.html template with the registration result message
    return render_template('candidate_registration.html', message=message, candidates=candidates)

@app.route('/register_voter', methods=['POST'])
def register_voter():
    # Handle voter registration here
    voter_id = int(request.form['voter_id'])
    voter_name = request.form['voter_name']

    message = voting_system.register_voter(voter_id, voter_name)

    # Render the index.html template with the registration result message
    return render_template('index.html', message=message)

@app.route('/vote', methods=['POST'])
def vote():
    # Handle the vote submission here
    voter_id = int(request.form['voter_id'])
    candidate_id = int(request.form['candidate_id'])

    # Ensure the voters dictionary is updated with the latest data from the database
    voting_system.load_voters_from_database()
    # Debugging statements
    #print("Voters dictionary:", voting_system.voters)

    # Check if the voter ID is valid
    if not voting_system.is_valid_voter(voter_id):
        #print(f"Invalid voter ID: {voter_id}. Voters: {voting_system.voters}")
        return render_template('index.html', message=f"Invalid voter ID: {voter_id}. Please enter a valid voter ID.")

    # Check if the voter is registered
    if voter_id not in voting_system.voters:
        #print(f"Voter {voter_id} is not in the voters dictionary. Voters: {voting_system.voters}")
        return render_template('index.html', message=f"Voter {voter_id} is not registered. Please register before voting.")

    # Check if the voter has already voted
    if voting_system.voters[voter_id]['has_voted']:
        #print(f"Voter {voter_id} has already voted. Voters: {voting_system.voters}")
        return render_template('index.html', message=f"Voter {voter_id} has already voted.")

    # Check if the candidate ID is valid
    if not voting_system.is_valid_candidate(candidate_id):
        #print(f"Invalid candidate ID: {candidate_id}. Voters: {voting_system.voters}")
        return render_template('index.html', message=f"Invalid candidate ID: {candidate_id}. Please choose a valid candidate.")

    # Attempt to cast the vote
    message = voting_system.vote(voter_id, candidate_id)

    # Check if the vote was successful
    if message is not None:
        #print(f"Vote successful. Message: {message}. Voters: {voting_system.voters}")
        return render_template('index.html', message=message)

    # Handle the case where cast_vote returned None (candidate not found in CSV)
    print(f"Candidate ID {candidate_id} not found in candidates.csv. Voters: {voting_system.voters}")
    return render_template('index.html', message=f"Candidate ID {candidate_id} not found in candidates.csv. Please choose a valid candidate.")
@app.route('/voting_over')
def voting_over():
    # Redirect to the result page when "Voting Over" is clicked
    return redirect(url_for('result'))
@app.route('/result')
def result():
    # Perform any result calculation logic here
    # ...
    decrypted_votes=voting_system.load_and_decode_votes()
    results=voting_system.candidate_vote_count(decrypted_votes)
    # Render the result.html template
    return render_template('result.html', results=results)

if __name__ == '__main__':
    # Run the app with debug mode
    app.run(debug=True,host='0.0.0.0',port=5000)
