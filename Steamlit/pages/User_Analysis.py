import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
import seaborn as sns
from collections import Counter


st.set_page_config(
    page_title='REPO SENTINEL', page_icon='computer')
hide_st_style = """
            <style>
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)
st.write(
    '<style>div.block-container{padding-top:2rem;}</style>', unsafe_allow_html=True)
style = "<style>h2 {text-align:;}</style>"
st.markdown(style, unsafe_allow_html=True)

# Function to detect outliers and display a graph for a parameter


def detect_outliers(df, parameter, contamination=0.05, custom_cmap='coolwarm'):
    df_numeric = df[[parameter]]
    df_numeric.fillna(0, inplace=True)

    model = IsolationForest(contamination=contamination)
    model.fit(df_numeric)

    outliers = model.predict(df_numeric)
    outliers = outliers == -1

    # Visualize the results
    fig, ax = plt.subplots(figsize=(8, 6))

    # Set a different colormap for the graph
    scatter = ax.scatter(df.index, df_numeric[parameter], s=100,
                         label=parameter, alpha=0.5, c=outliers, cmap=custom_cmap)

    ax.set_xlabel('Data Point Index')
    ax.set_ylabel(parameter)
    ax.set_title(f'Isolation Forest for {parameter}')

    # Annotate the points with names for outliers
    outlier_names = [name if is_outlier else '' for name,
                     is_outlier in zip(df['Contributor'], outliers)]
    for i, name in enumerate(outlier_names):
        if name:
            ax.annotate(
                name, (df.index[i], df_numeric[parameter][i]), color='red')

    # Create a colorbar for the outlier points
    cbar = fig.colorbar(scatter, ax=ax)
    cbar.set_label('Outlier', rotation=270)

    st.pyplot(fig)

    return outlier_names


# Main Streamlit app
st.title("Vulnerable User Detection")
st.sidebar.title("Upload Data")
# Add a sidebar for uploading the Excel file
uploaded_file = st.sidebar.file_uploader("Upload an Excel file", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, sheet_name="Sheet1")

    # Exclude non-numeric columns (e.g., 'Contributor' and 'Name')
    non_numeric_columns = ['Contributor', 'Name']
    df_numeric = df.drop(columns=non_numeric_columns)

    # Define custom colormaps for each parameter
    custom_colormaps = {
        'Followers': 'viridis',
        'Following': 'plasma',
        'Public Repositories': 'PiYG',
        'Contributions to Repository': 'magma',
        'Commit Frequency (All Repos)': 'PRGn',
        'Total Forks of Repos Contributed To': 'coolwarm',
        'Total Stars of Repos Contributed To': 'Spectral',
        'Number of Organizations': 'bwr'
    }

    # Store outlier information for each parameter
    outlier_info = {}

    # Iterate over the parameters and detect outliers
    parameters = df_numeric.columns
    for parameter in parameters:
        st.subheader(f"Parameter: {parameter}")
        custom_cmap = custom_colormaps.get(
            parameter, 'coolwarm')  # Default to 'coolwarm'
        # detect_outliers(df, parameter, custom_cmap=custom_cmap)
        outlier_names = detect_outliers(df, parameter, custom_cmap=custom_cmap)
        outlier_info[parameter] = [name for name in outlier_names if name]

    # Create a table showing parameters with their respective outliers
    st.subheader("Outlier Information by Parameter")

    parameter_outliers = []

    for parameter in outlier_info:
        # Calculate the range and threshold for the parameter
        # min_value = min(df[parameter])
        # max_value = max(df[parameter])
        # range_value = max_value - min_value
        # threshold = range_value / 2

        threshold = df[parameter].mean()

        # Determine the type of outlier for each contributor
        outlier_type = []

        for outlier_name in outlier_info[parameter]:
            # Get the numeric value of the outlier based on the parameter
            outlier_value = df[df['Contributor'] ==
                               outlier_name][parameter].values[0]
            outlier_float = float(outlier_value)
            outlier_type.append('Negative' if abs(
                outlier_float) < threshold else 'Positive')

        # Create a list of dictionaries for each parameter
        parameter_outliers.extend(
            [{"Parameter": parameter, "Outlier": contributor, "Type": outlier_type[i]}
                for i, contributor in enumerate(outlier_info[parameter])]
        )

    # Display the parameter names, their respective outliers, and their types (positive/negative)
    st.table(parameter_outliers)


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    # Determine the most occurring outlier
    all_outliers = [name for names in outlier_info.values() for name in names]
    # most_common_outlier, count = Counter(all_outliers).most_common(1)[0]

    # Determine the most common count of outliers
    outlier_counts = Counter(all_outliers)
    max_count = max(outlier_counts.values())

    # Find all outliers with the maximum count
    most_common_outliers = [outlier for outlier,
                            count in outlier_counts.items() if count == max_count]

    # Show the most occurring outliers
    st.subheader("Most Occurring Outliers")
    st.write(
        f"The most occurring outliers with a count of {max_count} are: {', '.join(most_common_outliers)}")
