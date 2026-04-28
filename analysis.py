"""
analysis.py
Additional socio-economic analysis modules for the web app.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import statsmodels.api as sm

def descriptive_stats(df, variables):
    """
    Compute descriptive statistics for selected variables.
    """
    stats = df[variables].describe().T
    stats['median'] = df[variables].median()
    stats['mode'] = df[variables].mode().iloc[0] if not df[variables].mode().empty else np.nan
    return stats.round(2)

def correlation_analysis(df, variables):
    """
    Compute correlation matrix and create heatmap.
    """
    corr = df[variables].corr()
    fig = px.imshow(corr, text_auto=True, aspect="auto", title="变量相关性矩阵")
    fig.update_layout(template='plotly_white')
    return fig

def simple_regression(df, x_var, y_var):
    """
    Perform simple linear regression.
    """
    X = df[[x_var]]
    y = df[y_var]
    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)

    fig = px.scatter(df, x=x_var, y=y_var, trendline="ols", title=f"{x_var} vs {y_var} 简单线性回归")
    fig.update_layout(template='plotly_white')

    # Add regression equation
    slope = model.coef_[0]
    intercept = model.intercept_
    equation = f"y = {slope:.2f}x + {intercept:.2f}, R² = {r2:.2f}"
    fig.add_annotation(text=equation, xref="paper", yref="paper", x=0.05, y=0.95, showarrow=False)

    return fig, {'slope': slope, 'intercept': intercept, 'r2': r2}

def multiple_regression(df, x_vars, y_var):
    """
    Perform multiple linear regression.
    """
    X = df[x_vars]
    y = df[y_var]
    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()

    summary = model.summary()
    return str(summary)

def scatter_plot(df, x_var, y_var, color_var=None, sample_size=5000):
    """
    Create scatter plot with optional color.
    """
    display_df = df.sample(n=min(sample_size, len(df)), random_state=42)
    if color_var:
        fig = px.scatter(display_df, x=x_var, y=y_var, color=color_var, title=f"{x_var} vs {y_var}")
    else:
        fig = px.scatter(display_df, x=x_var, y=y_var, title=f"{x_var} vs {y_var}")
    fig.update_layout(template='plotly_white')
    return fig

def histogram_plot(df, variable, bins=30):
    """
    Create histogram for a variable.
    """
    fig = px.histogram(df, x=variable, nbins=bins, title=f"{variable} 分布直方图")
    fig.update_layout(template='plotly_white')
    return fig

def box_plot(df, variable, group_var=None):
    """
    Create box plot for a variable, optionally grouped.
    """
    if group_var:
        fig = px.box(df, x=group_var, y=variable, title=f"{variable} 按 {group_var} 分组箱线图")
    else:
        fig = px.box(df, y=variable, title=f"{variable} 箱线图")
    fig.update_layout(template='plotly_white')
    return fig