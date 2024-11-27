import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_curve, auc
import numpy as np
import json
from shapely.geometry import shape

#viz
import matplotlib.pyplot as plt
import seaborn as sns
from shapely.geometry import mapping
import folium
from branca.colormap import LinearColormap

        
    

def analyze_zoning_probabilities(ground_truth_data, plan_data):
    """
    Main function to analyze zoning probabilities with visualization
    """
    analyzer = ZoningAnalyzer()
    
    # Prepare and train
    X, y, merged_data = analyzer.prepare_features(ground_truth_data, plan_data)
    X_train, X_test, y_train, y_test = analyzer.train_model(X, y)
    
    # Evaluate model
    evaluation_results = analyzer.evaluate_model(X_train, X_test, y_train, y_test)
    
    # Generate predictions
    probabilities = analyzer.predict_probabilities(X_test)
    
    # Create visualizations
    analyzer.visualize_results(evaluation_results, merged_data, probabilities)
    
    # Create spatial visualization
    spatial_map = analyzer.create_spatial_visualization(merged_data, probabilities)
    
    return analyzer, evaluation_results, probabilities, spatial_map

# ---------------------------------------------------------------------------------

class ZoningAnalyzer:
    def __init__(self):
        self.label_encoder = LabelEncoder()
        self.scaler = StandardScaler()
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.feature_names = None
    
    def prepare_features(self, ground_truth_data, plan_data):
        """
        Prepare features from ground truth and plan data
        
        Parameters:
        ground_truth_data: GeoDataFrame with current land use and ecosystem values
        plan_data: DataFrame with future zoning plans
        """
        # Merge spatial and attribute data
        merged_data = gpd.sjoin(ground_truth_data, plan_data, how='inner', predicate='intersects')
        
        # Calculate area-based features
        merged_data['area_ratio'] = merged_data.geometry.area / merged_data['total_area']
        
        # Create feature columns for ecosystem service values
        eco_features = ['eco_value_' + str(i) for i in range(1, 6)]  # Assuming 5 ecosystem service types
        for feature in eco_features:
            if feature not in merged_data.columns:
                merged_data[feature] = 0
        
        # Calculate statistics for ecosystem services within each zone
        eco_stats = merged_data.groupby('zone_id')[eco_features].agg(['mean', 'std', 'min', 'max'])
        eco_stats.columns = [f"{col[0]}_{col[1]}" for col in eco_stats.columns]
        
        # Prepare features for modeling
        feature_columns = (eco_stats.columns.tolist() + 
                         ['area_ratio', 'current_landuse', 'planned_gfa'])
        
        X = merged_data[feature_columns]
        y = merged_data['zoning_designation']
        
        # Store feature names for later use
        self.feature_names = feature_columns
        
        # Encode categorical variables
        categorical_columns = ['current_landuse']
        for col in categorical_columns:
            X[col] = self.label_encoder.fit_transform(X[col])
        
        # Scale numerical features
        X_scaled = self.scaler.fit_transform(X)
        
        return X_scaled, y, merged_data
    
    def train_model(self, X, y):
        """
        Train the Random Forest model and perform evaluation
        """
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        self.model.fit(X_train, y_train)
        
        return X_train, X_test, y_train, y_test
    
    def evaluate_model(self, X_train, X_test, y_train, y_test):
        """
        Comprehensive model evaluation
        """
        evaluation_results = {}
        
        # Basic predictions
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)
        
        # Classification report
        evaluation_results['classification_report'] = classification_report(y_test, y_pred)
        
        # Confusion matrix
        evaluation_results['confusion_matrix'] = confusion_matrix(y_test, y_pred)
        
        # Cross-validation scores
        cv_scores = cross_val_score(self.model, X_train, y_train, cv=5)
        evaluation_results['cv_scores'] = {
            'mean': cv_scores.mean(),
            'std': cv_scores.std(),
            'scores': cv_scores
        }
        
        # ROC curves and AUC scores
        n_classes = len(np.unique(y_test))
        roc_curves = {}
        for i in range(n_classes):
            fpr, tpr, _ = roc_curve(y_test == i, y_pred_proba[:, i])
            roc_auc = auc(fpr, tpr)
            roc_curves[f'class_{i}'] = {
                'fpr': fpr,
                'tpr': tpr,
                'auc': roc_auc
            }
        evaluation_results['roc_curves'] = roc_curves
        
        return evaluation_results
    
    def visualize_results(self, evaluation_results, merged_data, probabilities=None):
        """
        Create visualizations for model results
        """
        # Set up the visualization style
        plt.style.use('seaborn')
        
        # 1. Confusion Matrix Heatmap
        plt.figure(figsize=(10, 8))
        sns.heatmap(evaluation_results['confusion_matrix'], 
                   annot=True, fmt='d', cmap='Blues')
        plt.title('Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.show()
        
        # 2. ROC Curves
        plt.figure(figsize=(10, 8))
        for class_name, roc_data in evaluation_results['roc_curves'].items():
            plt.plot(roc_data['fpr'], roc_data['tpr'], 
                    label=f'{class_name} (AUC = {roc_data["auc"]:.2f})')
        plt.plot([0, 1], [0, 1], 'k--')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('ROC Curves')
        plt.legend()
        plt.show()
        
        # 3. Feature Importance Plot
        importance_df = self.get_feature_importance()
        plt.figure(figsize=(12, 6))
        sns.barplot(x='importance', y='feature', data=importance_df.head(10))
        plt.title('Top 10 Feature Importance')
        plt.show()
        
        # 4. Cross-validation Scores
        plt.figure(figsize=(8, 6))
        sns.boxplot(x=evaluation_results['cv_scores']['scores'])
        plt.title('Cross-validation Scores Distribution')
        plt.xlabel('Score')
        plt.show()
        
    def create_spatial_visualization(self, gdf, probabilities=None):
        """
        Create interactive spatial visualization using folium
        
        Parameters:
        gdf: GeoDataFrame with geometry
        probabilities: Predicted probabilities for each zone
        """
        # Create base map
        center = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]
        m = folium.Map(location=center, zoom_start=12)
        
        if probabilities is not None:
            # Add probability layers
            for class_name in probabilities.columns:
                # Create a choropleth layer for each class probability
                colormap = LinearColormap(
                    colors=['#fee5d9', '#fcae91', '#fb6a4a', '#de2d26', '#a50f15'],
                    vmin=probabilities[class_name].min(),
                    vmax=probabilities[class_name].max()
                )
                
                gjson = folium.GeoJson(
                    gdf.__geo_interface__,
                    style_function=lambda feature: {
                        'fillColor': colormap(probabilities.loc[feature['id'], class_name]),
                        'color': 'black',
                        'weight': 1,
                        'fillOpacity': 0.7
                    }
                )
                
                gjson.add_to(m)
                colormap.add_to(m)
                
        return m
    
    def predict_probabilities(self, new_data):
        """
        Predict probabilities for new zoning areas
        """
        # Prepare new data similar to training data
        for col in new_data.select_dtypes(include=['object']).columns:
            new_data[col] = self.label_encoder.transform(new_data[col])
        
        new_data_scaled = self.scaler.transform(new_data)
        probabilities = self.model.predict_proba(new_data_scaled)
        
        # Create DataFrame with probabilities
        prob_df = pd.DataFrame(
            probabilities,
            columns=self.label_encoder.classes_,
            index=new_data.index
        )
        
        return prob_df
    
    def get_feature_importance(self):
        """
        Get feature importance scores
        """
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        })
        return feature_importance.sort_values('importance', ascending=False)
    
    def plot_confusion_matrix(self, evaluation_results):
        """Create plotly confusion matrix heatmap"""
        conf_matrix = evaluation_results['confusion_matrix']
        
        fig = go.Figure(data=go.Heatmap(
            z=conf_matrix,
            x=self.label_encoder.classes_,
            y=self.label_encoder.classes_,
            text=conf_matrix,
            texttemplate="%{text}",
            textfont={"size": 12},
            colorscale='Blues'
        ))
        
        fig.update_layout(
            title='Confusion Matrix',
            xaxis_title='Predicted Label',
            yaxis_title='True Label',
            height=600
        )
        
        return fig
    
    def plot_roc_curves(self, evaluation_results):
        """Create plotly ROC curves"""
        fig = go.Figure()
        
        for class_name, roc_data in evaluation_results['roc_curves'].items():
            fig.add_trace(go.Scatter(
                x=roc_data['fpr'],
                y=roc_data['tpr'],
                name=f'{class_name} (AUC = {roc_data["auc"]:.2f})',
                mode='lines'
            ))
        
        fig.add_trace(go.Scatter(
            x=[0, 1],
            y=[0, 1],
            name='Random',
            line=dict(dash='dash', color='gray'),
            mode='lines'
        ))
        
        fig.update_layout(
            title='ROC Curves',
            xaxis_title='False Positive Rate',
            yaxis_title='True Positive Rate',
            height=600
        )
        
        return fig
    
    def plot_feature_importance(self):
        """Create plotly feature importance bar plot"""
        importance_df = self.get_feature_importance()
        
        fig = px.bar(
            importance_df.head(10),
            x='importance',
            y='feature',
            orientation='h',
            title='Top 10 Feature Importance'
        )
        
        fig.update_layout(height=600)
        return fig
    
    def plot_cv_scores(self, evaluation_results):
        """Create plotly box plot for cross-validation scores"""
        fig = go.Figure()
        
        fig.add_trace(go.Box(
            y=evaluation_results['cv_scores']['scores'],
            name='CV Scores'
        ))
        
        fig.update_layout(
            title='Cross-validation Scores Distribution',
            yaxis_title='Score',
            height=400
        )
        
        return fig

#the app
st.set_page_config(layout="wide", page_title="ARVO dev")

st.title("Zoning Designation Analysis")

# File upload section
st.header("Data Upload")
col1, col2 = st.columns(2)

with col1:
    ground_truth_file = st.file_uploader(
        "Upload Ground Truth Data (GeoJSON/GeoPackage)",
        type=['geojson', 'gpkg']
    )

with col2:
    plan_file = st.file_uploader(
        "Upload Planning Data (GeoJSON/GeoPackage)",
        type=['geojson', 'gpkg']
    )

if ground_truth_file and plan_file:
    # Load and process data
    try:
        if ground_truth_file.name.endswith('.geojson'):
            ground_truth_data = gpd.read_file(ground_truth_file)
        else:
            ground_truth_data = gpd.read_file(ground_truth_file.name)
            
        if plan_file.name.endswith('.geojson'):
            plan_data = gpd.read_file(plan_file)
        else:
            plan_data = gpd.read_file(plan_file.name)
        
        # Initialize analyzer
        analyzer = ZoningAnalyzer()
        
        with st.spinner("Processing data and training model..."):
            # Prepare and train model
            X, y, merged_data = analyzer.prepare_features(ground_truth_data, plan_data)
            X_train, X_test, y_train, y_test = analyzer.train_model(X, y)
            
            # Evaluate model
            evaluation_results = analyzer.evaluate_model(X_train, X_test, y_train, y_test)
            probabilities = analyzer.predict_probabilities(X_test)
        
        # Dashboard layout
        st.header("Model Performance")
        
        # Metrics row
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        
        with metric_col1:
            cv_mean = evaluation_results['cv_scores']['mean']
            st.metric("Mean CV Score", f"{cv_mean:.3f}")
        
        with metric_col2:
            cv_std = evaluation_results['cv_scores']['std']
            st.metric("CV Score Std", f"{cv_std:.3f}")
        
        with metric_col3:
            n_classes = len(evaluation_results['roc_curves'])
            st.metric("Number of Classes", n_classes)
        
        # Plots row 1
        st.subheader("Model Evaluation Plots")
        plot_col1, plot_col2 = st.columns(2)
        
        with plot_col1:
            conf_matrix_fig = analyzer.plot_confusion_matrix(evaluation_results)
            st.plotly_chart(conf_matrix_fig, use_container_width=True)
        
        with plot_col2:
            roc_curves_fig = analyzer.plot_roc_curves(evaluation_results)
            st.plotly_chart(roc_curves_fig, use_container_width=True)
        
        # Plots row 2
        plot_col3, plot_col4 = st.columns(2)
        
        with plot_col3:
            feature_importance_fig = analyzer.plot_feature_importance()
            st.plotly_chart(feature_importance_fig, use_container_width=True)
        
        with plot_col4:
            cv_scores_fig = analyzer.plot_cv_scores(evaluation_results)
            st.plotly_chart(cv_scores_fig, use_container_width=True)
        
        # Spatial visualization
        st.header("Spatial Analysis")
        
        # Convert GeoDataFrame to GeoJSON for Plotly
        geojson = json.loads(merged_data.to_json())
        
        # Create choropleth map for each probability class
        selected_class = st.selectbox(
            "Select Zoning Class for Visualization",
            options=probabilities.columns
        )
        
        fig = px.choropleth_mapbox(
            probabilities,
            geojson=geojson,
            locations=probabilities.index,
            color=selected_class,
            color_continuous_scale="Viridis",
            mapbox_style="carto-positron",
            zoom=9,
            center={"lat": merged_data.geometry.centroid.y.mean(), 
                    "lon": merged_data.geometry.centroid.x.mean()},
            opacity=0.5,
            title=f"Probability Distribution for {selected_class}"
        )
        
        fig.update_layout(height=800)
        st.plotly_chart(fig, use_container_width=True)
        
        # Download section
        st.header("Download Results")
        
        # Convert results to CSV
        probabilities_csv = probabilities.to_csv().encode('utf-8')
        st.download_button(
            label="Download Probability Predictions",
            data=probabilities_csv,
            file_name="zoning_probabilities.csv",
            mime="text/csv"
        )
        
    except Exception as e:
        st.error(f"Error processing data: {str(e)}")

else:
    st.info("Please upload both ground truth and planning data files to begin analysis.")
