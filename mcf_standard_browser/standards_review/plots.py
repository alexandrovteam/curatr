from plotly.offline import plot
import plotly.graph_objs as go
import numpy as np

def fragment_plot(xdata, ydata, label):
    data  = [
            go.Scatter(
                x=xdata,
                y=ydata,
                mode='markers',
                error_y = go.ErrorY(
                    symmetric=False,
                    arrayminus=np.zeros(ydata.shape),
                    array=-ydata,
                    width=0
                ),
                hoverinfo="x",
                text=xdata,
                name=label
        ),]

    layout = dict(title = 'Fragmentation Spectrum',
              xaxis = dict(title = 'm/z'),
              yaxis = dict(title = 'Intensity'),

              )

    fig = go.Figure(data=data, layout=layout)
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    return plot_div

def xic_plot(xic_x, xic_y, pts_x, pts_y, timeunit='s'):
    xicTrace = go.Scatter(
            x=xic_x,
            y=xic_y,
            mode='line',
            name='xic'
        )
    ptsTrace = go.Scatter(
            x=pts_x,
            y=pts_y,
            marker = go.Marker(
                size=10,
                color='black',
                symbol='triangle-down'
            ),
            mode='markers',
            name='ms/ms points'
        )
    data = [xicTrace, ptsTrace]
    layout = dict(title='XIC',
                  xaxis=dict(title='time ({})'.format(timeunit)),
                  yaxis=dict(title='Intensity'),
                  )

    fig = go.Figure(data=data, layout=layout)
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    return plot_div