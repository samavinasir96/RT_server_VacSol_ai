from fileinput import filename
from flask import Flask, make_response, request, send_file, send_from_directory
from flask_cors import CORS, cross_origin
from flask_restful import Api, Resource, reqparse
import real_time_server
import pickle
import pandas as pd
import os
import sys

app = Flask(__name__)
api = Api(app)
CORS(app)

@app.route("/upload", methods=["POST"])
def upload():
    sequence = request.form.get("sequence")
    sequence = sequence.replace("\n", "")
    file = request.files.get("file")
    try:
        if sequence:
            print(f"sequence={sequence}")
            # get the path of the directory where the script is located
            script_dir = sys.path[0]
            # concatenate the script directory with the filename to create the full path of the FASTA file
            file_path = os.path.join(script_dir, "sequences.fasta")
            print(f"file_path={file_path}")
            # Open the file in write mode
            with open(file_path, "w") as f:
                # Write the sequence to the file
                f.write(sequence)
                print(f"written to file")
        elif file:
            # Use the save method to save the file to the current directory
            file_path = os.path.join(script_dir, "sequences.fasta")
            file.save(file_path)
        
        file_path = os.path.join(script_dir, "sequences.fasta")
        real_time_server.calculate_features(file_path)
    except Exception as e:
        print(f"Error analyzing sequence: {e}")
        return "Error analyzing sequence", 500
    return {'status': 'success'}, 200

@app.route("/results", methods=["GET"])
def get_results():
    try:
        script_dir = sys.path[0]
        model_path = os.path.join(script_dir, "svm_model.pkl")   
        with open(model_path, "rb") as file:
            model = pickle.load(file)

        csv_path = os.path.join(script_dir, "Rescaled_CSV.csv")
        df = pd.read_csv(csv_path)
        feature_cols = df.drop(labels=['Protein_ID'], axis=1)

        x_new = feature_cols.values

        out = model.predict(x_new)
        results = pd.DataFrame({'Protein_ID': df['Protein_ID'], 'Prediction': out})

    except Exception as e:
        print(f"Error analyzing sequence: {e}")
        return "Error analyzing sequence", 500
    return {row['Protein_ID']: int(row['Prediction']) for _, row in results.iterrows()}, 200


if __name__ == "__main__":
    app.run(host=os.environ.get('IP', '0.0.0.0'))
