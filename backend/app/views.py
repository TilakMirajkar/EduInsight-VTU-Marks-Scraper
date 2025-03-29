from django.shortcuts import render
from django.views.generic import FormView
from .forms import ScraperForm
from .scraper import ResultScraperService
import pandas as pd
from django.contrib import messages
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import base64
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile


class ScraperView(FormView):
    template_name = 'app/automate.html'
    form_class = ScraperForm
    
    def form_valid(self, form):
        prefix_usn = form.cleaned_data['prefix_usn'].upper()
        usn_range = form.cleaned_data['usn_range']
        sem = form.cleaned_data['sem']
        url = form.cleaned_data['url']
        is_reval = 'RV' in url
        
        scraper_service = ResultScraperService()
        
        try:
            response = scraper_service.execute_scraping(prefix_usn, usn_range, url, is_reval)
            if response:
                messages.success(self.request, "Scraping successful, returning Excel file.")
                return response
            else:
                form.add_error(None, "No data was retrieved. Please check your inputs.")
                return self.form_invalid(form)

        except Exception as e:
            form.add_error(None, f"Error during scraping: {str(e)}")
            return self.form_invalid(form)
        
# def insights(request):
#     table_html = None
#     filters = None
#     error_message = None
#     analysis_data = {}
#     chart_images = []

#     if request.method == 'POST' and request.FILES.get('file'):
#         uploaded_file = request.FILES['file']
#         file_path = default_storage.save(f"uploads/{uploaded_file.name}", ContentFile(uploaded_file.read()))

#         try:
#             df = pd.read_excel(default_storage.open(file_path))
#             filters = df.columns.tolist()
#             table_html = df.to_html(classes="table-auto w-full border-collapse border border-gray-300 text-sm")

#             # 🔹 Basic Statistics
#             analysis_data["Summary Statistics"] = df.describe().to_html(classes="table-auto w-full border-collapse border text-sm")
#             analysis_data["Missing Values"] = df.isnull().sum().to_frame().to_html(classes="table-auto w-full border-collapse border text-sm")
#             analysis_data["Top 5 Records"] = df.head().to_html(classes="table-auto w-full border-collapse border text-sm")

#             # 🔹 Generating Charts (Histograms, Correlation Heatmap, etc.)
#             def generate_chart(fig):
#                 buffer = BytesIO()
#                 fig.savefig(buffer, format="png")
#                 buffer.seek(0)
#                 encoded_img = base64.b64encode(buffer.getvalue()).decode()
#                 plt.close(fig)
#                 return f"data:image/png;base64,{encoded_img}"

#             # 🎯 Histogram for Numerical Columns
#             num_cols = df.select_dtypes(include=[np.number]).columns
#             for col in num_cols:
#                 fig, ax = plt.subplots(figsize=(6, 4))
#                 sns.histplot(df[col].dropna(), bins=20, kde=True, ax=ax)
#                 ax.set_title(f"Distribution of {col}")
#                 chart_images.append(generate_chart(fig))

#             # 🎯 Correlation Heatmap
#             if len(num_cols) > 1:
#                 fig, ax = plt.subplots(figsize=(8, 6))
#                 sns.heatmap(df[num_cols].corr(), annot=True, cmap="coolwarm", ax=ax)
#                 ax.set_title("Correlation Heatmap")
#                 chart_images.append(generate_chart(fig))

#             # 🔹 Save Analysis to the Same Excel File (New Sheet)
#             with pd.ExcelWriter(default_storage.path(file_path), mode="a", engine="openpyxl") as writer:
#                 df.describe().to_excel(writer, sheet_name="Statistics")
#                 df.isnull().sum().to_frame().to_excel(writer, sheet_name="Missing Values")
#                 df.head().to_excel(writer, sheet_name="Top 5 Records")

#         except Exception as e:
#             error_message = f"Error processing file: {str(e)}"

#     return render(request, 'app/insights.html', {
#         'table': table_html,
#         'filters': filters,
#         'error': error_message,
#         'analysis_data': analysis_data,
#         'chart_images': chart_images
#     })

from django.shortcuts import render
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
import json

def insights(request):
    table_html = None
    filters = None
    error_message = None
    analysis_data = {}
    chart_images = []
    grade_distributions = {}
    subject_performance = {}
    performance_metrics = {}
    
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        file_path = default_storage.save(f"uploads/{uploaded_file.name}", ContentFile(uploaded_file.read()))
        
        try:
            # Read the Excel file
            df = pd.read_excel(default_storage.open(file_path))
            filters = df.columns.tolist()
            table_html = df.to_html(classes="table-auto w-full border-collapse border border-gray-300 text-sm")
            
            # Identify potential student ID, name, and marks columns
            # This is a heuristic approach - adjust based on your expected file format
            potential_id_cols = [col for col in df.columns if any(id_term in col.lower() for id_term in ['id', 'roll', 'no', 'number'])]
            potential_name_cols = [col for col in df.columns if any(name_term in col.lower() for name_term in ['name', 'student'])]
            
            # Assume remaining numeric columns might be subject marks
            potential_mark_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            # Remove columns that might be IDs
            potential_mark_cols = [col for col in potential_mark_cols if col not in potential_id_cols]
            
            # 🔹 Basic Statistics
            analysis_data["Summary Statistics"] = df.describe().to_html(classes="table-auto w-full border-collapse border text-sm")
            analysis_data["Missing Values"] = df.isnull().sum().to_frame().to_html(classes="table-auto w-full border-collapse border text-sm")
            analysis_data["Top 5 Records"] = df.head().to_html(classes="table-auto w-full border-collapse border text-sm")
            
            # Function to generate chart images
            def generate_chart(fig):
                buffer = BytesIO()
                fig.savefig(buffer, format="png", bbox_inches="tight", dpi=100)
                buffer.seek(0)
                encoded_img = base64.b64encode(buffer.getvalue()).decode()
                plt.close(fig)
                return f"data:image/png;base64,{encoded_img}"
            
            # 🎯 Advanced Analysis for Marks Data
            
            # 1. Overall Performance Metrics
            if potential_mark_cols:
                df_marks = df[potential_mark_cols]
                
                # Calculate total and percentage if appropriate
                if 'Total' not in df.columns and len(potential_mark_cols) > 1:
                    df['Total'] = df_marks.sum(axis=1)
                    max_possible = df_marks.count(axis=1) * 100  # Assuming each subject is out of 100
                    df['Percentage'] = (df['Total'] / max_possible) * 100
                    
                    # Add to analysis data
                    performance_metrics["Overall Statistics"] = df[['Total', 'Percentage']].describe().to_html(
                        classes="table-auto w-full border-collapse border text-sm"
                    )
                
                # 2. Grade Distribution (based on percentage)
                if 'Percentage' in df.columns:
                    def assign_grade(percentage):
                        if percentage >= 90: return 'A+'
                        elif percentage >= 80: return 'A'
                        elif percentage >= 70: return 'B+'
                        elif percentage >= 60: return 'B'
                        elif percentage >= 50: return 'C'
                        elif percentage >= 40: return 'D'
                        else: return 'F'
                    
                    df['Grade'] = df['Percentage'].apply(assign_grade)
                    grade_counts = df['Grade'].value_counts().sort_index()
                    grade_distributions["Grade Distribution"] = grade_counts.to_frame().to_html(
                        classes="table-auto w-full border-collapse border text-sm"
                    )
                    
                    # Grade Distribution Chart
                    fig, ax = plt.subplots(figsize=(8, 6))
                    sns.countplot(x='Grade', data=df, order=['A+', 'A', 'B+', 'B', 'C', 'D', 'F'], palette='viridis', ax=ax)
                    ax.set_title("Grade Distribution")
                    ax.set_xlabel("Grade")
                    ax.set_ylabel("Number of Students")
                    for p in ax.patches:
                        ax.annotate(f'{int(p.get_height())}', 
                                    (p.get_x() + p.get_width() / 2., p.get_height()), 
                                    ha = 'center', va = 'bottom')
                    chart_images.append(generate_chart(fig))
                
                # 3. Subject-wise Performance
                for col in potential_mark_cols:
                    if df[col].dtype in [np.int64, np.float64]:
                        subject_stats = {
                            'Average': df[col].mean(),
                            'Median': df[col].median(),
                            'Max': df[col].max(),
                            'Min': df[col].min(),
                            'Pass Rate': (df[col] >= 40).mean() * 100,  # Assuming 40 is pass mark
                            'Distinction Rate': (df[col] >= 75).mean() * 100  # Assuming 75 is distinction mark
                        }
                        subject_performance[col] = subject_stats
                
                # Subject Performance Chart
                if len(potential_mark_cols) > 0:
                    avg_marks = [df[col].mean() for col in potential_mark_cols]
                    pass_rates = [(df[col] >= 40).mean() * 100 for col in potential_mark_cols]
                    
                    fig, ax1 = plt.subplots(figsize=(10, 6))
                    ax1.set_title("Subject-wise Performance")
                    ax1.set_xlabel("Subject")
                    ax1.set_ylabel("Average Marks", color='tab:blue')
                    ax1.bar(potential_mark_cols, avg_marks, color='tab:blue', alpha=0.7)
                    ax1.tick_params(axis='y', labelcolor='tab:blue')
                    ax1.set_ylim(0, 100)
                    
                    ax2 = ax1.twinx()
                    ax2.set_ylabel("Pass Rate (%)", color='tab:red')
                    ax2.plot(potential_mark_cols, pass_rates, 'ro-', linewidth=2)
                    ax2.tick_params(axis='y', labelcolor='tab:red')
                    ax2.set_ylim(0, 100)
                    
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()
                    chart_images.append(generate_chart(fig))
            
            # 4. Histogram for each subject
            for col in potential_mark_cols:
                if df[col].dtype in [np.int64, np.float64]:
                    fig, ax = plt.subplots(figsize=(8, 5))
                    sns.histplot(df[col].dropna(), bins=20, kde=True, ax=ax)
                    ax.set_title(f"Distribution of Marks in {col}")
                    ax.set_xlabel("Marks")
                    ax.set_ylabel("Frequency")
                    
                    # Add mean and median lines
                    ax.axvline(df[col].mean(), color='red', linestyle='--', label=f'Mean: {df[col].mean():.2f}')
                    ax.axvline(df[col].median(), color='green', linestyle='-.', label=f'Median: {df[col].median():.2f}')
                    ax.legend()
                    
                    chart_images.append(generate_chart(fig))
            
            # 5. Correlation Heatmap between subjects
            if len(potential_mark_cols) > 1:
                fig, ax = plt.subplots(figsize=(10, 8))
                correlation_matrix = df[potential_mark_cols].corr()
                mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))
                sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm", mask=mask, ax=ax, fmt=".2f")
                ax.set_title("Correlation Between Subjects")
                chart_images.append(generate_chart(fig))
            
            # 6. Identify Struggling and Exceptional Students
            if 'Total' in df.columns and any(potential_name_cols):
                name_col = potential_name_cols[0]  # Use the first identified name column
                
                # Top 10 performers
                top_students = df.nlargest(10, 'Total')[[name_col, 'Total', 'Percentage']]
                analysis_data["Top Performers"] = top_students.to_html(classes="table-auto w-full border-collapse border text-sm")
                
                # Students needing attention (bottom 10%)
                threshold = df['Percentage'].quantile(0.1)
                struggling_students = df[df['Percentage'] <= threshold][[name_col, 'Total', 'Percentage']]
                analysis_data["Students Needing Attention"] = struggling_students.to_html(classes="table-auto w-full border-collapse border text-sm")
            
            # 7. Comparative Analysis Chart (Box Plot)
            if len(potential_mark_cols) > 1:
                fig, ax = plt.subplots(figsize=(12, 8))
                df_melted = df[potential_mark_cols].melt()
                sns.boxplot(x='variable', y='value', data=df_melted, ax=ax)
                ax.set_title("Comparative Performance Across Subjects")
                ax.set_xlabel("Subject")
                ax.set_ylabel("Marks")
                plt.xticks(rotation=45, ha='right')
                chart_images.append(generate_chart(fig))
            
            # 8. Percentage Distribution
            if 'Percentage' in df.columns:
                fig, ax = plt.subplots(figsize=(8, 6))
                sns.histplot(df['Percentage'].dropna(), bins=20, kde=True, ax=ax)
                ax.set_title("Distribution of Overall Percentage")
                ax.set_xlabel("Percentage")
                ax.set_ylabel("Frequency")
                # Add lines for different grade thresholds
                for threshold, grade in [(40, 'Pass'), (60, 'B'), (80, 'A')]:
                    ax.axvline(threshold, color='red', linestyle='--', 
                              label=f'{grade} Threshold: {threshold}%')
                ax.legend()
                chart_images.append(generate_chart(fig))
            
            # 🔹 Save Analysis to Excel with additional insights
            with pd.ExcelWriter(default_storage.path(file_path), mode="a", engine="openpyxl") as writer:
                df.describe().to_excel(writer, sheet_name="Statistics")
                df.isnull().sum().to_frame().to_excel(writer, sheet_name="Missing Values")
                
                # Save performance by subject
                if subject_performance:
                    pd.DataFrame(subject_performance).to_excel(writer, sheet_name="Subject Performance")
                
                # Save grade distribution if available
                if 'Grade' in df.columns:
                    df['Grade'].value_counts().sort_index().to_excel(writer, sheet_name="Grade Distribution")
                
                # Save correlation matrix
                if len(potential_mark_cols) > 1:
                    df[potential_mark_cols].corr().to_excel(writer, sheet_name="Correlations")
                
                # Save enhanced dataframe with calculated fields
                if 'Total' in df.columns and 'Percentage' in df.columns:
                    df.to_excel(writer, sheet_name="Enhanced Data")
            
            # Convert dict data to JSON for the template
            subject_performance_json = json.dumps(subject_performance)
            
        except Exception as e:
            error_message = f"Error processing file: {str(e)}"
            # Log the full traceback for debugging
            import traceback
            print(traceback.format_exc())
    
    return render(request, 'app/insights.html', {
        'table': table_html,
        'filters': filters,
        'error': error_message,
        'analysis_data': analysis_data,
        'chart_images': chart_images,
        'grade_distributions': grade_distributions,
        'subject_performance': subject_performance,
        'performance_metrics': performance_metrics
    })