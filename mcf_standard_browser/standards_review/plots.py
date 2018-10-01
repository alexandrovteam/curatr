from plotly.offline import plot
import plotly.graph_objs as go
import numpy as np

def fragment_plot(xdata, ydata, label):
    data  = [
            go.Scatter(
                x=xdata,
                y=ydata,
                mode='markers',
                marker=go.Marker(
                    size=1,
                ),
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

    layout = dict(
              xaxis = dict(title = 'm/z'),
              yaxis = dict(title = 'Intensity'),

              )

    fig = go.Figure(data=data, layout=layout)
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    return plot_div

def xic_plot(xic_x, xic_y, pts_x, pts_y, timeunit='min'):
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

def multixic(plotData, timeunit='min'):
    """

    Args:
        plotData: [(xic_x, xic_y, pts_x, pts_y),]
        timeunit: label string default = 'min'

    Returns: plotly graph object

    """
    traces = []
    for xic_x, xic_y, pts_x, pts_y in plotData:
        traces.append( go.Scatter(
                x=xic_x,
                y=xic_y,
                mode='line',
                name='xic'
            )
        )
        traces.append(
            go.Scatter(
                x=pts_x,
                y=pts_y,
                marker=go.Marker(
                    size=10,
                    color='black',
                    symbol='triangle-down'
                ),
                mode='markers',
                name='ms/ms points'
            )
        )
    layout = dict(title='XIC',
                  xaxis=dict(title='time ({})'.format(timeunit)),
                  yaxis=dict(title='Intensity'),
                  )

    fig = go.Figure(data=traces, layout=layout)
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    return plot_div

def donut(data, labels, name="", title="", label=""):
    traces = [
            {
                "values": data,
                "labels": labels,
                "name": name,
                "hoverinfo": "label+percent+name",
                "hole": .4,
                "type": "pie"
            },
        ]
    layout = {
            "title": title,
            "annotations": [
                {
                    "font": {
                        "size": 20
                    },
                    "showarrow": False,
                    "text": label,
                    "x": 0.5,
                    "y": 0.5
                },
                ],
        "autosize": True
    }
    fig = go.Figure(data=traces, layout=layout)
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    return plot_div

def bar(data, labels, name="", title="", xlabel="", ylabel="", reverse=False):
    if reverse:
        labels = list(reversed(labels))
        data = list(reversed(data))
    print(">>>>>>", xlabel, ylabel, data, labels)
    traces = [
            {
                "x": labels,
                "y": data,
                "name": name,
                "hoverinfo": "label+percent+name",
                "type": "bar"
            },
        ]
    layout = dict(title=title,
                  xaxis=dict(title=xlabel),
                  yaxis=dict(title=ylabel),
                  )
    fig = go.Figure(data=traces, layout=layout)
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    return plot_div
