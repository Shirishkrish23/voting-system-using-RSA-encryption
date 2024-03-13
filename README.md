# Online-Voting-System-using-RSA

This repository contains a Python implementation of a basic voting system using Flask as the web framework and MySQL as the database management system. The system allows users to register voters and candidates, cast votes, and view the voting results.

## Usage

### Registration

*Candidate Registration*: Candidates can be registered by providing their ID, name, and age through the candidate registration form.

*Voter Registration*: Voters can be registered by providing their ID and name through the voter registration form.

### Voting

Once registered, voters can cast their votes by selecting a candidate from the list and submitting their vote.

## Results

The results page displays the current voting results, including the number of votes received by each candidate.

## Features

*Candidate and Voter Registration*: Allows registration of candidates and voters with unique IDs.

*Voting*: Enables voters to cast their votes for registered candidates or for NOTA (None of the Above).

*Result Calculation*: Calculates and displays the voting results based on the cast votes.

## Architecture Overview

*Flask*: Flask is used as the web framework to handle HTTP requests and responses.

*MySQL*: MySQL is utilized as the database management system for storing candidate and voter information, as well as voting data.

*RSA Encryption*: Votes are encrypted using RSA encryption before being stored in the database to ensure confidentiality.

*Web Interface*: The web interface is designed using HTML templates rendered by Flask, allowing users to interact with the system through a browser.

## Contributors 

* Shirish Krishna S
* Manjunath K P
