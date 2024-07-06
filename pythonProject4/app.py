from flask import Flask, request, render_template, redirect, url_for
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

import matplotlib
matplotlib.use('Agg')

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
PLOT_FOLDER = 'static/plots'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PLOT_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

dataframes = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'csvFile' not in request.files:
        return redirect(request.url)

    file = request.files['csvFile']
    if file.filename == '':
        return redirect(request.url)

    if file and file.filename.endswith('.csv'):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        df = pd.read_csv(filepath)
        dataframes[file.filename] = df
        return redirect(url_for('dashboard', filename=file.filename))

@app.route('/dashboard/<filename>', methods=['GET', 'POST'])
def dashboard(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    df = dataframes.get(filename)

    if request.method == 'POST':
        if 'insert' in request.form:
            new_row = {col: request.form[col] for col in df.columns}
            new_row_df = pd.DataFrame([new_row])
            df = pd.concat([df, new_row_df], ignore_index=True)
        elif 'update' in request.form:
            index = int(request.form['index'])
            for col in df.columns:
                df.at[index, col] = request.form[col]
        elif 'delete' in request.form:
            index = int(request.form['index'])
            df = df.drop(index).reset_index(drop=True)

        df.to_csv(filepath, index=False)
        dataframes[filename] = df

    summary = df.describe().T

    plot_dir = os.path.join('static', 'plots')
    os.makedirs(plot_dir, exist_ok=True)

    plot_paths = []
    for column in df.select_dtypes(include=['float64', 'int64']).columns:
        plt.figure(figsize=(10, 6))
        sns.histplot(df[column], kde=True)
        plot_path = os.path.join(plot_dir, f'{column}.png')
        plt.savefig(plot_path)
        plt.close()
        plot_paths.append(f'plots/{column}.png')

    insights = []
    for column in df.select_dtypes(include=['float64', 'int64']).columns:
        column_mean = df[column].mean()
        column_median = df[column].median()
        column_std = df[column].std()
        insights.append({
            'column': column,
            'mean': column_mean,
            'median': column_median,
            'std': column_std,
            'max': df[column].max(),
            'min': df[column].min()
        })

    return render_template('dashboard.html', tables=[df.to_html(classes='data')], titles=df.columns.values,
                           plot_paths=plot_paths, summary=summary.to_html(classes='data'), insights=insights)

if __name__ == '__main__':
    app.run(debug=True)
