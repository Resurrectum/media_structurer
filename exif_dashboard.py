import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.express as px
import os
from datetime import datetime
from PIL import Image
import numpy as np
import write_date_to_exif as wde

app = dash.Dash(__name__)

# List of image paths
image_paths = [os.path.join(root, file) for root, dirs, files in os.walk('/home/rafael/Downloads/datalake/no_exif_jpg') for file in files if file.lower().endswith('.jpg')]

# Read the image into an array
img = Image.open(image_paths[0])
img_array = np.array(img)

app.layout = html.Div([
    dcc.Graph(id='image', figure=px.imshow(img_array)),
    dcc.DatePickerSingle(id='date-picker', date=datetime.today(), display_format='DD/MM/YYYY'),
    dcc.Input(id='time-input', type='time', value='00:00'),
    html.Button('Submit', id='submit-button', n_clicks=0),
    html.Div(id='output'),
    html.Div(id='image-path', children=f'Image path: {image_paths[0]}')
])

@app.callback(
    Output('image', 'figure'),
    Output('output', 'children'),
    Output('image-path', 'children'),
    Input('submit-button', 'n_clicks'),
    State('date-picker', 'date'),
    State('time-input', 'value'),
    State('image', 'figure')
)
def update_image(n_clicks, date, time, figure):
    if n_clicks > 0:
        # Combine the date and time into a datetime object
        date_time = datetime.strptime(f'{date} {time}', '%Y-%m-%d %H:%M')
        # Write the selected date and time to the EXIF data of the current image
        wde(figure.data[0].source, date_time)
        # Load the next image
        next_image_path = image_paths[n_clicks % len(image_paths)]
        img = Image.open(next_image_path)
        img_array = np.array(img)
        figure = px.imshow(img_array)
        return figure, f'Successfully updated EXIF data of {figure.data[0].source} and loaded next image {next_image_path}', f'Image path: {next_image_path}'
    return figure, '', f'Image path: {image_paths[0]}'
if __name__ == '__main__':
    app.run_server(debug=True)
    