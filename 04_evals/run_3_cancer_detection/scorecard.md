# HALLUCINATION EVAL SCORECARD (EVALUATION SUMMARY)

This file contains the final evaluation summaries and detailed evidence logs produced by the SciSpace Hallucination Evaluator.

## 📊 Evaluation Summary Matrix

| Pipeline Stage | Metric | Score | Details |
| :--- | :--- | :---: | :--- |
| **Stage 1: Query** | **Intent Coverage** | **Skipped** | 0/0 intents covered |
| **Stage 2a: Alignment** | **Directional Alignment** | **Skipped** | 0/0 intents addressed |
| **Stage 2b: Extraction** | **Data Extraction Accuracy** | **Skipped** | Check of spreadsheet cells vs. paper abstracts |
| **Stage 2c: Synthesis** | **Synthesis Faithfulness** | **Skipped** | Check of report claims vs. spreadsheet rows |
| **Stage 3a: Grounding** | **Overall Claim Reliability** | **32.7%** | 33/101 non-common claims supported |
| **Stage 3b: Grounding** | **Cited Grounding Rate** | **66.0%** | 33/50 cited claims supported |

---

## 🛡️ Stage 1: Search Query Intent Coverage Evidence

*Skipped (missing intent coverage logs)*


---

## 🗺️ Stage 2a: Directional Alignment Evidence

*Skipped (missing directional alignment logs)*


---

## 🗄️ Stage 2b: Data Extraction Accuracy Evidence Table

*Skipped (missing data extraction logs or schema mismatch)*


---

## 🧩 Stage 2c: Synthesis Faithfulness Evidence Table

*Skipped (missing synthesis faithfulness logs or schema mismatch)*


---

## 📚 Stage 3: Claim-Level Fact-Checking Evidence Tables

This section partitions all factual claims extracted from the final report into detailed evidence tables. Each table shows the exact report text, the cited text verbatim, the evaluator's explanation, and the grounding verdict.

### Table 3a: Factual Hallucinations (Unsupported, Overstated, or Contradicted)

| Report Claim | Citations | Verdict | Source Paper Says (Verbatim Abstract) | Contrast Evidence / Hallucination Detail |
| :--- | :--- | :---: | :--- | :--- |
| CNN ensemble applied to prostate mpMRI achieved median AUC of 0.88. | [4] | UNSUPPORTED | AI-based technologies achieved a median AUC-ROC of 0.88 (range 0.70–0.93) | The source states that AI-based technologies achieved a median AUC-ROC of 0.88, but it does not specify that a CNN ensemble was used or that this result is specifically from a CNN ensemble applied to prostate mpMRI. |
| CNN ensemble applied to prostate mpMRI achieved median sensitivity of 86%. | [4] | UNSUPPORTED | AI-based technologies achieved median sensitivity of 0.86. | The source does not mention CNN ensemble; it only reports a median sensitivity of 86% for AI-based technologies broadly. |
| Ensemble ML on blood cfDNA/methylation achieved AUC up to 0.993 for multi-cancer detection. | [11] | UNSUPPORTED | The maximum values of the assessment indicators such as ... area under the curve (AUC) in included studies were ... 0.9929 | The source reports a maximum AUC of 0.9929 across all studies but does not mention 'Ensemble ML on blood cfDNA/methylation' or 'multi-cancer detection' specifically. |
| Genomic/omics AI meta-analysis reported AUC range approximately 0.90–0.993. | [11] | UNSUPPORTED | The maximum values of the assessment indicators such as ... area under the curve (AUC) in included studies were ... 0.9929 | The source reports a maximum AUC of 0.9929, not a range of approximately 0.90–0.993 as claimed. |
| Small cohort sizes and risk of overfitting are concerns in high-performance genomics AI reports. | [10], [11] | UNSUPPORTED | Source 10 discusses lack of large-scale clinical validation studies for MCED tests; Source 11 reviews AI techniques in precision medicine without addressing cohort sizes or overfitting. | Neither source mentions small cohort sizes or risk of overfitting in high-performance genomics AI reports. |
| Assay standardization challenges exist across platforms and laboratories for genomics-based AI. | [10] | UNSUPPORTED | The source discusses MCED tests combining molecular analysis with AI but does not address assay standardization challenges. | The source does not mention assay standardization challenges across platforms and laboratories for genomics-based AI. |
| SHAP-guided random forest and CNN fusion of CT imaging and gene expression for lung cancer achieved AUC 0.963. | [7] | OVERSTATED | The fusion of genomic and imaging modalities significantly enhances classification performance, achieving an AUC of 96.3% | The source reports an AUC of 96.3%, not 0.963, and the claim uses a different numeric format (0.963) which is equivalent but the source does not mention 'SHAP-guided random forest and CNN fusion' as the method; it describes a multi-modal framework with Random Forest and CNN+VAE, and the claim's phrasing is more specific and less qualified than the source. |
| Integrated heterogeneous data types, missing modalities, and multi-site alignment are challenges for multimodal AI. | [12], [14] | UNSUPPORTED | The sources present frameworks that fuse imaging, clinical, and demographic data (LungGuard) or histopathological images, genomic profiles, and clinical information (cervical cancer framework), and mention multi-centre data but not as a challenge. | The sources describe multimodal AI systems and their successes but do not discuss challenges such as integrated heterogeneous data types, missing modalities, or multi-site alignment. |
| Most gains of multimodal AI are demonstrated on retrospective datasets. | [12], [13] | UNSUPPORTED | The lung cancer source mentions training on a multi-centre dataset and future work in prospective cohorts; the cervical cancer source describes using cohorts but does not specify retrospective or prospective. | Neither source discusses the proportion of multimodal AI gains demonstrated on retrospective versus prospective datasets; they only describe their own studies. |
| Most high-performing AI models are validated retrospectively; prospective randomized clinical trials are rare. | [10], [12], [4] | UNSUPPORTED | Source [12] implies its own model validation was not yet prospective (future work aims at prospective cohorts), and source [4] concludes that 'large-scale prospective trials are required to validate clinical integration.' | The source abstracts do not state that most high-performing AI models are validated retrospectively, nor do they explicitly claim that prospective randomized clinical trials are rare; they only note a need for large-scale prospective trials, which does not directly confirm the claim. |
| Small cohorts relative to model complexity inflate reported performance, especially in genomics. | [10], [11] | UNSUPPORTED | The sources focus on MCED tests and a systematic review of AI in precision medicine, without addressing cohort size or performance inflation. | Neither source discusses small cohorts relative to model complexity or inflated performance, especially in genomics. |
| Models trained on single-institution data often underperform on external datasets. | [3], [4] | UNSUPPORTED | Source 3 discusses generalization from UK to USA, and Source 4 mentions methodological heterogeneity restricting generalizability, but neither directly addresses the claim. | The source texts discuss AI performance in breast cancer screening and prostate cancer detection, but do not mention training on single-institution data or underperformance on external datasets. |
| False-positive rates in CT lung nodule detection and mammography remain clinically significant. | [2], [6] | UNSUPPORTED | For CT: 'specificity remained variable'; for mammography: no mention of false-positive rates. | The source for CT lung nodule detection mentions variable specificity but does not state that false-positive rates are clinically significant, and the mammography source does not discuss false-positive rates. |
| Tissue-of-origin misclassification in MCED tests is a key barrier to clinical deployment. | [10] | UNSUPPORTED | The abstract lists 'major factors which are preventing clinical implementation' but does not specify tissue-of-origin misclassification. | The source does not mention tissue-of-origin misclassification as a barrier; it only notes that large-scale clinical validation studies are lacking. |
| Requiring paired, synchronized data from multiple modalities reduces available training datasets and complicates real-world deployment. | [12], [14] | UNSUPPORTED | Both abstracts focus on the benefits and performance of multimodal fusion, with no mention of data pairing limitations or deployment challenges. | Neither source discusses any reduction in available training datasets or complications in real-world deployment caused by requiring paired, synchronized multimodal data. |
| The NHS-Galleri trial in the UK is evaluating blood-based MCED tests in population screening contexts. | [10] | UNSUPPORTED | The abstract discusses MCED tests generally and notes that large-scale clinical validation studies are still lacking, but does not reference any specific trial. | The source text does not mention the NHS-Galleri trial or any specific UK trial evaluating blood-based MCED tests in population screening contexts. |
| SHAP values, GradCAM, and attention visualization are increasingly integrated into cancer detection pipelines. | [7] | UNSUPPORTED | Grad-CAM and SHAP techniques validate salient radiomic features; no mention of attention visualization or increasing integration. | The source describes a single study using SHAP and Grad-CAM but does not mention attention visualization or state that these methods are increasingly integrated into cancer detection pipelines. |

### Table 3b: Faithful Grounded Claims (Supported)

| Report Claim | Citations | Source Paper Says (Verbatim Abstract) | Grounding Proof |
| :--- | :--- | :--- | :--- |
| Large-scale deployment studies and head-to-head comparisons with radiologists have been reported, particularly in breast and lung cancer screening. | [1], [2], [3] | Source 2: 'This systematic review compares the diagnostic accuracy... of AI algorithms and radiologists in identifying lung nodules'; Source 3: 'an AI system... outperformed all of the human readers'. | Source 2 is a systematic review comparing AI and radiologists for lung nodule detection, and Source 3 evaluates an AI system for breast cancer screening that outperforms radiologists, directly supporting the claim of head-to-head comparisons in both cancer types. |
| Breast cancer detection using mammography plus ultrasound multimodal imaging with deep learning fusion achieved an AUC of 0.968. | [5] | AUC (0.968 (95% CI:0.947-0.989)) | The source explicitly states that the multimodal classification model achieved an AUC of 0.968 (95% CI:0.947-0.989), which matches the claim. |
| Breast cancer detection using mammography plus ultrasound multimodal imaging with deep learning fusion achieved a specificity of 96.41%. | [5] | Experimental results demonstrate that the multimodal classification model outperforms single-modal models in terms of specificity (96.41% (95% CI:93.10%-99.72%)) | The source explicitly states that the multimodal classification model achieved a specificity of 96.41%. |
| AI CAD applied to longitudinal screening mammography achieved AUC of 0.63–0.67. | [6] | For all time points combined, excluding screen detection, the area under the receiver operating characteristic curve (AUC) ranged from 0.63 to 0.67 for the three AI CAD systems | The source states that for all time points combined, excluding screen detection, the AUC ranged from 0.63 to 0.67 for the three AI CAD systems. |
| AI CAD applied to longitudinal screening mammography achieved sensitivity of 13–25% for pre-diagnostic detection. | [6] | At 90% specificity, the proportion of cancers potentially flagged by AI-1, AI-2, and AI-3 was 12.7%, 13.8%, and 17.0% at 10 years before diagnosis; 19.0%, 19.6%, and 19.7% at 6 years; and 24.2%, 23.3%, and 25.2% at 4 years. | The source reports proportions of cancers flagged at 90% specificity for various years before diagnosis, ranging from 12.7% to 25.2%, which matches the claim's 13–25% sensitivity range for pre-diagnostic detection. |
| AI CAD applied to longitudinal screening mammography achieved specificity fixed at 90%. | [6] | At 90% specificity, the proportion of cancers potentially flagged by AI-1, AI-2, and AI-3 was ... | The source explicitly states that the AI CAD systems were evaluated at a fixed 90% specificity, reporting proportions of cancers flagged at that threshold. |
| CNN ensemble applied to prostate mpMRI achieved median specificity of 83%. | [4] | AI-based technologies achieved a median AUC-ROC of 0.88 (range 0.70–0.93), with median sensitivity and specificity of 0.86 and 0.83, respectively. | The source states that AI-based technologies achieved a median specificity of 0.83, which directly matches the claim's median specificity of 83%. |
| CNN-based lung CT nodule detection improved sensitivity compared to baseline. | [2] | AI models achieved higher sensitivity, especially with nodules <6mm | The source states that AI models, which include CNNs, achieved higher sensitivity in lung nodule detection, directly supporting the claim of improvement over baseline. |
| Deep learning mammography for international breast screening was non-inferior to radiologists. | [3] | the AI system maintained non-inferior performance and reduced the workload of the second reader by 88% | The source states that in a simulation of double-reading, the AI system maintained non-inferior performance compared to radiologists, and the evaluation used data from the UK and USA, supporting the claim of non-inferiority for international breast screening. |
| Deep learning mammography reduced reader workload. | [3] | the AI system maintained non-inferior performance and reduced the workload of the second reader by 88% | The source explicitly states that the AI system reduced the workload of the second reader by 88% in a simulation of the double-reading process. |
| Direct comparison with radiologist performance is available for imaging-based AI. | [3] | In an independent study of six radiologists, the AI system outperformed all of the human readers | The source explicitly states that the AI system outperformed all six radiologists in an independent study, providing a direct comparison with radiologist performance. |
| Dataset heterogeneity across scanners, institutions, and annotation protocols reduces generalizability of imaging-based AI. | [4], [2] | methodological heterogeneity and limited standardization restrict generalizability | The first source explicitly states that 'methodological heterogeneity and limited standardization restrict generalizability', which directly supports the claim about dataset heterogeneity reducing generalizability. |
| False positives remain a persistent challenge in imaging-based AI, leading to specificity variability. | [2], [6] | AI models achieved higher sensitivity... however, specificity remained variable. | The first source states that AI models achieved higher sensitivity but 'specificity remained variable', which directly supports the claim that false positives remain a challenge leading to specificity variability. |
| There is limited prospective validation of imaging-based AI in real-world screening workflows. | [4], [3] | Prostate review: 'Large-scale prospective trials are required to validate clinical integration.' Breast paper: 'paves the way for clinical trials to improve the accuracy and efficiency of breast cancer screening.' | Both sources indicate that prospective validation in real-world screening is lacking: the prostate review calls for large-scale prospective trials, and the breast cancer study is retrospective and paves the way for future clinical trials. |
| Genomics-based AI approaches are promising for multi-cancer early detection because they are non-invasive and cancer-type agnostic. | [10] | MCED tests combine molecular analysis of tumor-related markers in body fluids with AI to simultaneously detect a variety of cancers, are minimally invasive, and depict great potential for clinical application. | The source describes MCED tests as minimally invasive and capable of detecting multiple cancers simultaneously, which aligns with the claim's 'non-invasive' and 'cancer-type agnostic' attributes, and states they have 'great potential'. |
| ML spectral classifier on SERS serum artificial nose achieved 100% sensitivity for NSCLC detection. | [9] | Using an optimized multireceptor array, the model achieves 100% sensitivity at 98% specificity | The source explicitly states that the model achieves 100% sensitivity for NSCLC detection. |
| ML spectral classifier on SERS serum artificial nose achieved 98% specificity for NSCLC detection. | [9] | the model achieves 100% sensitivity at 98% specificity | The source explicitly states that the model achieves 98% specificity for NSCLC detection. |
| 1D-CNN + LSTM on urine proteomics achieved AUC 0.98 for pancreatic cancer detection. | [8] | the area under curve (AUC) of 98% | The source explicitly states that the 1D-CNN + LSTM model achieved an AUC of 98% for diagnosing pancreatic cancer using urine biomarkers. |
| 1D-CNN + LSTM on urine proteomics achieved 97% accuracy for pancreatic cancer detection. | [8] | our proposed 1-D CNN + LSTM model achieved the best accuracy score of 97% | The source explicitly states that the 1-D CNN + LSTM model achieved 97% accuracy for diagnosing pancreatic cancers using urine biomarkers. |
| Most blood-based multi-cancer early detection tests are not yet clinically validated at population scale. | [10] | large-scale clinical validation studies are still lacking | The source states that 'large-scale clinical validation studies are still lacking' for MCED tests, which directly supports the claim that most are not yet clinically validated at population scale. |
| Multimodal AI systems consistently demonstrate performance gains over single-modality approaches. | [7], [12], [13], [14] | The fusion of genomic and imaging modalities significantly enhances classification performance (AUC 96.3% vs. 91.8% imaging alone and 89.7% gene expression alone); multimodal solution reaches up to AUC 0.96 and is significantly better than unimodal; the model registers a 95.88% diagnostic accuracy and AUC of 0.98, highlighting improvements. | Each cited source reports that multimodal fusion outperforms single-modality approaches, with quantitative results showing higher AUC and accuracy for the multimodal models. |
| Semi-supervised deep fusion of histopathology, genomics, and clinical data for cervical cancer achieved AUC 0.98. | [14] | its Area Under the Curve (AUC) of 0.98 is testament to its high discriminative ability. | The source explicitly states that the model achieved an AUC of 0.98. |
| Semi-supervised deep fusion of histopathology, genomics, and clinical data for cervical cancer achieved sensitivity 96%. | [14] | the model registering a ... sensitivity of 96% | The source explicitly states that the model achieved a sensitivity of 96%, matching the claim exactly. |
| Semi-supervised deep fusion of histopathology, genomics, and clinical data for cervical cancer achieved specificity 94%. | [14] | the model registering a 95.88% diagnostic accuracy, sensitivity of 96%, and specificity of 94% | The source explicitly states that the model achieved a specificity of 94%. |
| LungGuard 3D-CNN fusion of low-dose CT, biomarkers, and demographics for lung cancer achieved AUC 0.96. | [12] | Preliminary results show that LungGuard achieves AUC ≈ 0.96, sensitivity ≈ 92%, specificity ≈ 90% in early-stage (I & II) lung cancer detection | The source explicitly states that LungGuard achieves AUC ≈ 0.96 in early-stage lung cancer detection. |
| LungGuard 3D-CNN fusion of low-dose CT, biomarkers, and demographics for lung cancer achieved sensitivity approximately 92%. | [12] | Preliminary results show that LungGuard achieves AUC ≈ 0.96, sensitivity ≈ 92%, specificity ≈ 90% in early-stage (I & II) lung cancer detection | The source explicitly states that LungGuard achieves sensitivity approximately 92% in early-stage lung cancer detection. |
| LungGuard 3D-CNN fusion of low-dose CT, biomarkers, and demographics for lung cancer achieved specificity approximately 90%. | [12] | Preliminary results show that LungGuard achieves ... specificity ≈ 90% in early-stage (I & II) lung cancer detection | The source explicitly states that LungGuard achieves specificity ≈ 90% in early-stage lung cancer detection. |
| Multimodal AI using visual, genomic, and clinical features for cervical cancer achieved high performance. | [13] | The multimodal solution reached up to AUC 0.96 and was significantly better than unimodal. | The source explicitly states that the multimodal AI solution reached an AUC of 0.96, which indicates high performance. |
| SHAP and attention maps enable clinical interpretability in multimodal AI. | [7] | Grad-CAM and SHAP techniques validate salient radiomic features... By combining high predictive accuracy with interpretability across data types, the proposed framework advances radiogenomic lung cancer detection while setting a precedent for deploying trustworthy AI systems in precision oncology. | The source explicitly states that SHAP and Grad-CAM techniques validate salient radiomic features and that the framework combines high predictive accuracy with interpretability across data types, which directly supports the claim that SHAP and attention maps enable clinical interpretability in multimodal AI. |
| Imaging alone (CT-CNN) for lung cancer detection achieved AUC of 91.8%. | [7] | achieving an AUC of 96.3%, compared to 91.8% with imaging alone and 89.7% with gene expression alone. | The source explicitly states that imaging alone achieved an AUC of 91.8%. |
| Genomics alone (gene expression RF) for lung cancer detection achieved AUC of 89.7%. | [7] | The fusion of genomic and imaging modalities significantly enhances classification performance, achieving an AUC of 96.3%, compared to 91.8% with imaging alone and 89.7% with gene expression alone. | The source explicitly states that gene expression alone achieved an AUC of 89.7%. |
| Multimodal fusion for lung cancer detection achieved AUC of 96.3%. | [7] | The fusion of genomic and imaging modalities significantly enhances classification performance, achieving an AUC of 96.3% | The source explicitly states that the fusion of genomic and imaging modalities achieved an AUC of 96.3%. |
| Fusion provided a +4.5 percentage point gain over the best single modality in lung radiogenomics. | [7] | The fusion of genomic and imaging modalities significantly enhances classification performance, achieving an AUC of 96.3%, compared to 91.8% with imaging alone and 89.7% with gene expression alone. | The source states fusion achieved 96.3% AUC versus 91.8% for imaging alone, a difference of 4.5 percentage points. |

### Table 3c: Uncited Factual Claims

| Report Claim | Verdict | Reasoning |
| :--- | :---: | :--- |
| Regulatory-cleared AI tools exist, including FDA-cleared CAD systems. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Imaging-based AI performance degrades for rare cancers with limited training data. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Very high AUCs (>0.99) in genomics studies often reflect small, homogeneous cohorts with potential overfitting. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Genomics-based AI can detect molecular alterations before imaging-detectable lesions. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Tissue-of-origin prediction accuracy in genomics-based AI varies, and misclassification can misdirect workup. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Multimodal AI systems can handle missing modalities with imputation or masking strategies. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Requiring paired imaging and molecular data significantly reduces available training cohorts for multimodal AI. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| 3D CNN fusion pipelines require substantial GPU resources. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Imaging-based AI achieved best AUC of 0.968. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Imaging-based AI achieved best sensitivity of 86% (median) for prostate cancer. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Imaging-based AI achieved best specificity of 96.41% for breast imaging. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Imaging-based AI has validation scale large, at population-scale. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Genomics-based AI achieved best AUC of 0.98–0.993. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Genomics-based AI achieved best sensitivity of 100% for NSCLC SERS. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Genomics-based AI achieved best specificity of 98% for NSCLC SERS. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Genomics-based AI validation scale is small to medium cohorts. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Multimodal fusion AI achieved best AUC of 0.98. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Multimodal fusion AI achieved best sensitivity of 96% for cervical cancer. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Multimodal fusion AI achieved best specificity of 94% for cervical cancer. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Multimodal fusion AI validation scale is medium, multi-centre. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Imaging AUC range is 0.63–0.97. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Genomics AUC range is 0.90–0.993. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Multimodal AUC range is 0.96–0.98. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Imaging sensitivity range is 13–100% (task-dependent). | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Genomics sensitivity range is high in small cohorts. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Multimodal sensitivity range is approximately 90–96%. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Imaging specificity range is 83–96%. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Genomics specificity range is 83–98%. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Multimodal specificity range is approximately 90–94%. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Imaging clinical maturity is four out of five stars. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Genomics clinical maturity is two out of five stars. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Multimodal clinical maturity is three out of five stars. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Imaging invasiveness is non-invasive. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Genomics invasiveness is minimally invasive. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Multimodal invasiveness varies. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Imaging data requirements are imaging archives. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Genomics data requirements are biobank plus assay data. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Multimodal data requirements are both imaging and genomic data plus clinical data. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Imaging scalability is high. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Genomics scalability is medium. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Multimodal scalability is low to medium. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Imaging explainability is medium using GradCAM. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Genomics explainability is low to medium. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Multimodal explainability is medium using SHAP and attention. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Imaging regulatory approval is partial with FDA-cleared CAD systems. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Genomics regulatory approval is limited. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Multimodal regulatory approval is none yet. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Few AI-based cancer screening tools have achieved broad clinical approval. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Large-scale pre-trained vision transformers such as CONCH and UNI are trained on millions of pathology images and enable zero-shot and few-shot cancer detection. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Federated learning enables training on distributed hospital datasets without sharing raw patient data. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |
| Post-market surveillance of FDA-cleared AI tools in mammography and lung CT screening is generating real-world performance data. | UNCITED | Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail. |

*No claims found for table 3d: other claims (unverifiable or common knowledge)*
