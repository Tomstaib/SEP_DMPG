import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns
import warnings
from graphviz import Digraph

from src.core.server import Server
from src.core.sink import Sink
from src.core.source import Source
from src.util.global_imports import Stats

warnings.simplefilter(action='ignore', category=FutureWarning)


def visualize_system() -> None:
    """
    Visualize the system using Graphviz.
    """
    dot = Digraph(comment='Simulation Model')

    # Advanced graph style attributes for an elegant look
    dot.attr(rankdir='LR', size='24,14', newrank='true')
    dot.attr(fontname='Open Sans', fontsize='12', fontcolor='grey')
    dot.attr('node', style='filled, rounded', color='lightgrey', fontname='Open Sans', fontsize='11')
    dot.attr('edge', arrowhead='vee', arrowsize='0.8', color='grey', fontname='Open Sans', fontsize='10')

    # Custom function color palette
    def get_color(value: int, max_value: int) -> str:
        """
        Convert a value to a color using a custom color palette. The color is based on the value's position in the range.

        :param value: Value to be converted to color
        :param max_value: Maximum value in the range
        :return: Color in hexadecimal format
        """
        norm_value = value / max_value if max_value != 0 else 0
        colors = plt.cm.Spectral(norm_value + 0.2)  # A visually rich color palette
        return mcolors.rgb2hex(colors)

    max_processed = max(server.entities_processed for server in Server.servers) if Server.servers else 1

    # Stylish node and edge design
    for source in Source.sources:
        label = f'{source.name}\nCreated: {source.entities_created_pivot_table}'
        dot.node(source.name, label=label, shape='diamond', fillcolor='#BDD7EE', fontcolor='black')

    for source in Source.sources:
        for next_server, _ in source.next_components:
            dot.edge(source.name, next_server.name, style='dashed', color='darkgreen')

    for server in Server.servers:
        color = get_color(server.entities_processed, max_processed)
        label = f'{server.name}\nProcessed: {server.entities_processed}'
        dot.node(server.name, label=label, shape='box', fillcolor=color, fontcolor='black')

        for next_component, prob in server.next_components:
            edge_style = 'bold' if prob else 'dotted'
            edge_label = f'{prob:.1f}%' if prob else ''
            dot.edge(server.name, next_component.name, label=edge_label, style=edge_style, color='darkblue')

    for sink in Sink.sinks:
        label = f'Sink\n{sink.name}\nProcessed: {sink.entities_processed}'
        dot.node(sink.name, label=label, shape='hexagon', fillcolor='#E6B8AF', fontcolor='black')

    # Advanced layout options for visual clarity
    dot.attr(overlap='scalexy', splines='true', nodesep='0.6', ranksep='2.0', bgcolor='whitesmoke')

    # Save and render the graph
    dot.render('simulation_model_pro', view=True)


def scatterplot(component_type: str, variable1: str, variable2: str) -> None:
    """
    Creates a scatterplot for a specific component type, using two variables that are displayed on two axes.
    Data is collected from `Stats.all_detailed_stats`, converted into a pandas DataFrame, and plotted using seaborn.

    :param component_type: Type of component (Server, Sink, Source, ...)
    :param variable1: First variable to plot
    :param variable2: Second variable to plot
    """
    # Collect data for scatterplot
    scatter_data = []
    for run_data in Stats.all_detailed_stats:
        component_stats = run_data.get(component_type, [])

        if component_type == 'Server':
            for server_stat in component_stats:
                value1 = server_stat.get(variable1, None)
                value2 = server_stat.get(variable2, None)
                if value1 is not None and value2 is not None:
                    scatter_data.append((server_stat['Server'], value1, value2))
        elif component_type in ['Sink', 'Source']:
            for component_name, component_stat in component_stats.items():
                value1 = component_stat.get(variable1, None)
                value2 = component_stat.get(variable2, None)
                if value1 is not None and value2 is not None:
                    scatter_data.append((component_name, value1, value2))

    # Convert data to DataFrame for plotting
    df = pd.DataFrame(scatter_data, columns=['Component', variable1, variable2])

    # Plotting the scatterplot
    plt.figure(figsize=(12, 8))
    sns.set(style="whitegrid", palette="muted")

    sns.scatterplot(data=df, x=variable1, y=variable2, hue='Component',
                    palette='cubehelix', s=100, edgecolor='w', alpha=0.7)

    plt.title(f'Scatterplot of {variable1} vs {variable2} for each {component_type}', fontsize=18, fontweight='bold')
    plt.xlabel(variable1, fontsize=14)
    plt.ylabel(variable2, fontsize=14)
    plt.legend(title='Component', bbox_to_anchor=(1.05, 1), loc='upper left')

    sns.despine()
    plt.show()


def histogram(component_type: str, variable: str) -> None:
    """
    Generates histograms for different types of components based on specified statistics.
    Each component's data is visualized in a separate subplot, showing the distribution of a given variable of interest alongside its mean and median values.

    :param component_type: Type of component (Server, Sink, Source, ...)
    :param variable: Variable to plot
    """
    # Collect data for histogram
    histogram_data = {}
    for run_data in Stats.all_detailed_stats:
        component_stats = run_data.get(component_type, [])

        if component_type == 'Server':
            for server_stat in component_stats:
                server_name = server_stat['Server']
                value = server_stat.get(variable, None)
                histogram_data.setdefault(server_name, []).append(value)
        elif component_type in ['Sink', 'Source']:
            for component_name, component_stat in component_stats.items():
                value = component_stat.get(variable, None)
                histogram_data.setdefault(component_name, []).append(value)
        else:
            value = component_stats.get(variable, None)
            histogram_data.setdefault(component_type, []).append(value)

    # Setting a theme
    sns.set(style="whitegrid", palette="muted")

    fig, axes = plt.subplots(len(histogram_data), 1, figsize=(12, 6 * len(histogram_data)))
    fig.tight_layout(pad=6.0)

    for i, (name, values) in enumerate(histogram_data.items()):
        ax = axes[i]
        sns.histplot(values, bins='auto', kde=True, color=sns.cubehelix_palette(start=.5, rot=-.75)[i],
                     ax=ax,
                     alpha=0.7)
        ax.set_title(f'{name} - {variable}', fontsize=16, fontweight='bold')
        ax.set_xlabel(variable, fontsize=14)
        ax.set_ylabel('Frequency', fontsize=14)

        mean_val = np.mean(values)
        median_val = np.median(values)
        ax.axvline(mean_val, color='crimson', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.2f}')
        ax.axvline(median_val, color='navy', linestyle=':', linewidth=2, label=f'Median: {median_val:.2f}')
        ax.legend(loc='upper right')

    plt.show()


def boxplot(component_type: str, variable: str) -> None:
    """
    Collects data for a boxplot from `Stats.all_detailed_stats` based on the component type and variable.
    It then creates boxplots and subplots for each component type and specified statistics,
    showing the distribution of the variable.

    :param component_type: Type of component (Server, Sink, Source, ...)
    :param variable: Variable to plot
    """
    # Collect data for boxplot
    boxplot_data = {}
    for run_data in Stats.all_detailed_stats:
        component_stats = run_data.get(component_type, [])

        if component_type == 'Server':
            for server_stat in component_stats:
                server_name = server_stat['Server']
                value = server_stat.get(variable, None)
                boxplot_data.setdefault(server_name, []).append(value)
        elif component_type in ['Sink', 'Source']:
            for component_name, component_stat in component_stats.items():
                value = component_stat.get(variable, None)
                boxplot_data.setdefault(component_name, []).append(value)
        else:
            value = component_stats.get(variable, None)
            boxplot_data.setdefault(component_type, []).append(value)

    # Plotting the boxplot
    fig, ax = plt.subplots(figsize=(12, 8))

    sns.boxplot(data=list(boxplot_data.values()), palette="viridis", ax=ax, showmeans=True,
                meanprops={"marker": "o", "markerfacecolor": "white", "markeredgecolor": "black"})

    # Set tick positions and labels
    ax.set_xticks(np.arange(len(boxplot_data)))
    ax.set_xticklabels(boxplot_data.keys(), fontsize=12, fontweight='bold')

    ax.set_title(f'Boxplot of {variable} for each {component_type}', fontsize=16, fontweight='bold')
    ax.set_xlabel('Component', fontsize=14)
    ax.set_ylabel(variable, fontsize=14)

    # Enhanced readability and styling
    plt.xticks(rotation=45)
    sns.despine(offset=10, trim=False)  # Changed trim to False
    ax.grid(True, linestyle='--', alpha=0.7, which='both')  # Ensure gridlines are displayed on all axes

    plt.show()


def violinplot(component_type: str, variable: str) -> None:
    """
    Generates violinplots for different types of components.
    Violin plots provide a visual representation of the variable distribution for a specific component type.

    :param component_type: Type of component (Server, Sink, Source, ...)
    :param variable: Variable to plot
    """
    # Collect data for violinplot
    violinplot_data = []
    for run_data in Stats.all_detailed_stats:
        component_stats = run_data.get(component_type, [])

        if component_type == 'Server':
            for server_stat in component_stats:
                value = server_stat.get(variable, None)
                if value is not None:
                    violinplot_data.append((server_stat['Server'], value))
        elif component_type in ['Sink', 'Source']:
            for component_name, component_stat in component_stats.items():
                value = component_stat.get(variable, None)
                if value is not None:
                    violinplot_data.append((component_name, value))
        else:
            value = component_stats.get(variable, None)
            if value is not None:
                violinplot_data.append((component_type, value))

    # Convert data to DataFrame for plotting
    df = pd.DataFrame(violinplot_data, columns=['Component', variable])

    # Plotting the violinplot
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(12, 8))
    sns.violinplot(data=df, x='Component', y=variable, hue='Component', palette="coolwarm", inner="quart", legend=False)

    plt.title(f'Violin Plot of {variable} for each {component_type}', fontsize=16)
    plt.xlabel('Component', fontsize=14)
    plt.ylabel(variable, fontsize=14)

    plt.show()
