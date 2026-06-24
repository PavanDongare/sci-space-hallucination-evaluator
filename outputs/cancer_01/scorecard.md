HALLUCINATION EVAL SCORECARD
=============================

Stage 1: Query Hallucination
  Skipped: missing query or search log.

Stage 2: Directional Faithfulness & Data Accuracy
  Skipped: missing intermediate report and consolidated table.

Stage 3: Claim-Level Fact-Checking
  Claim Reliability ............. 32.7%     (33/101 non-common factual claims supported)
  Cited Grounding Rate .......... 66.0%     (33/50 cited verifiable claims supported)
    - Supported ................. 33
    - Unsupported ............... 16
    - Contradicted .............. 0
    - Overstated ................ 1
    - Uncited factual claims .... 51
    - Not verifiable ............ 0
    - Common knowledge .......... 0

  X UNSUPPORTED:
    Claim: "CNN ensemble applied to prostate mpMRI achieved median AUC of 0.88."
    Source says: "AI-based technologies achieved a median AUC-ROC of 0.88 (range 0.70–0.93)"
    -> The source states that AI-based technologies achieved a median AUC-ROC of 0.88, but it does not specify that a CNN ensemble was used or that this result is specifically from a CNN ensemble applied to prostate mpMRI.

  X UNSUPPORTED:
    Claim: "CNN ensemble applied to prostate mpMRI achieved median sensitivity of 86%."
    Source says: "AI-based technologies achieved median sensitivity of 0.86."
    -> The source does not mention CNN ensemble; it only reports a median sensitivity of 86% for AI-based technologies broadly.

  X UNCITED:
    Claim: "Regulatory-cleared AI tools exist, including FDA-cleared CAD systems."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Imaging-based AI performance degrades for rare cancers with limited training data."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNSUPPORTED:
    Claim: "Ensemble ML on blood cfDNA/methylation achieved AUC up to 0.993 for multi-cancer detection."
    Source says: "The maximum values of the assessment indicators such as ... area under the curve (AUC) in included studies were ... 0.9929"
    -> The source reports a maximum AUC of 0.9929 across all studies but does not mention 'Ensemble ML on blood cfDNA/methylation' or 'multi-cancer detection' specifically.

  X UNSUPPORTED:
    Claim: "Genomic/omics AI meta-analysis reported AUC range approximately 0.90–0.993."
    Source says: "The maximum values of the assessment indicators such as ... area under the curve (AUC) in included studies were ... 0.9929"
    -> The source reports a maximum AUC of 0.9929, not a range of approximately 0.90–0.993 as claimed.

  X UNCITED:
    Claim: "Very high AUCs (>0.99) in genomics studies often reflect small, homogeneous cohorts with potential overfitting."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Genomics-based AI can detect molecular alterations before imaging-detectable lesions."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNSUPPORTED:
    Claim: "Small cohort sizes and risk of overfitting are concerns in high-performance genomics AI reports."
    Source says: "Source 10 discusses lack of large-scale clinical validation studies for MCED tests; Source 11 reviews AI techniques in precision medicine without addressing cohort sizes or overfitting."
    -> Neither source mentions small cohort sizes or risk of overfitting in high-performance genomics AI reports.

  X UNSUPPORTED:
    Claim: "Assay standardization challenges exist across platforms and laboratories for genomics-based AI."
    Source says: "The source discusses MCED tests combining molecular analysis with AI but does not address assay standardization challenges."
    -> The source does not mention assay standardization challenges across platforms and laboratories for genomics-based AI.

  X UNCITED:
    Claim: "Tissue-of-origin prediction accuracy in genomics-based AI varies, and misclassification can misdirect workup."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X OVERSTATED:
    Claim: "SHAP-guided random forest and CNN fusion of CT imaging and gene expression for lung cancer achieved AUC 0.963."
    Source says: "The fusion of genomic and imaging modalities significantly enhances classification performance, achieving an AUC of 96.3%"
    -> The source reports an AUC of 96.3%, not 0.963, and the claim uses a different numeric format (0.963) which is equivalent but the source does not mention 'SHAP-guided random forest and CNN fusion' as the method; it describes a multi-modal framework with Random Forest and CNN+VAE, and the claim's phrasing is more specific and less qualified than the source.

  X UNCITED:
    Claim: "Multimodal AI systems can handle missing modalities with imputation or masking strategies."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNSUPPORTED:
    Claim: "Integrated heterogeneous data types, missing modalities, and multi-site alignment are challenges for multimodal AI."
    Source says: "The sources present frameworks that fuse imaging, clinical, and demographic data (LungGuard) or histopathological images, genomic profiles, and clinical information (cervical cancer framework), and mention multi-centre data but not as a challenge."
    -> The sources describe multimodal AI systems and their successes but do not discuss challenges such as integrated heterogeneous data types, missing modalities, or multi-site alignment.

  X UNCITED:
    Claim: "Requiring paired imaging and molecular data significantly reduces available training cohorts for multimodal AI."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "3D CNN fusion pipelines require substantial GPU resources."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNSUPPORTED:
    Claim: "Most gains of multimodal AI are demonstrated on retrospective datasets."
    Source says: "The lung cancer source mentions training on a multi-centre dataset and future work in prospective cohorts; the cervical cancer source describes using cohorts but does not specify retrospective or prospective."
    -> Neither source discusses the proportion of multimodal AI gains demonstrated on retrospective versus prospective datasets; they only describe their own studies.

  X UNCITED:
    Claim: "Imaging-based AI achieved best AUC of 0.968."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Imaging-based AI achieved best sensitivity of 86% (median) for prostate cancer."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Imaging-based AI achieved best specificity of 96.41% for breast imaging."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Imaging-based AI has validation scale large, at population-scale."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Genomics-based AI achieved best AUC of 0.98–0.993."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Genomics-based AI achieved best sensitivity of 100% for NSCLC SERS."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Genomics-based AI achieved best specificity of 98% for NSCLC SERS."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Genomics-based AI validation scale is small to medium cohorts."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Multimodal fusion AI achieved best AUC of 0.98."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Multimodal fusion AI achieved best sensitivity of 96% for cervical cancer."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Multimodal fusion AI achieved best specificity of 94% for cervical cancer."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Multimodal fusion AI validation scale is medium, multi-centre."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Imaging AUC range is 0.63–0.97."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Genomics AUC range is 0.90–0.993."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Multimodal AUC range is 0.96–0.98."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Imaging sensitivity range is 13–100% (task-dependent)."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Genomics sensitivity range is high in small cohorts."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Multimodal sensitivity range is approximately 90–96%."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Imaging specificity range is 83–96%."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Genomics specificity range is 83–98%."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Multimodal specificity range is approximately 90–94%."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Imaging clinical maturity is four out of five stars."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Genomics clinical maturity is two out of five stars."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Multimodal clinical maturity is three out of five stars."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Imaging invasiveness is non-invasive."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Genomics invasiveness is minimally invasive."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Multimodal invasiveness varies."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Imaging data requirements are imaging archives."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Genomics data requirements are biobank plus assay data."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Multimodal data requirements are both imaging and genomic data plus clinical data."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Imaging scalability is high."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Genomics scalability is medium."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Multimodal scalability is low to medium."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Imaging explainability is medium using GradCAM."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Genomics explainability is low to medium."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Multimodal explainability is medium using SHAP and attention."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Imaging regulatory approval is partial with FDA-cleared CAD systems."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Genomics regulatory approval is limited."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Multimodal regulatory approval is none yet."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNSUPPORTED:
    Claim: "Most high-performing AI models are validated retrospectively; prospective randomized clinical trials are rare."
    Source says: "Source [12] implies its own model validation was not yet prospective (future work aims at prospective cohorts), and source [4] concludes that 'large-scale prospective trials are required to validate clinical integration.'"
    -> The source abstracts do not state that most high-performing AI models are validated retrospectively, nor do they explicitly claim that prospective randomized clinical trials are rare; they only note a need for large-scale prospective trials, which does not directly confirm the claim.

  X UNSUPPORTED:
    Claim: "Small cohorts relative to model complexity inflate reported performance, especially in genomics."
    Source says: "The sources focus on MCED tests and a systematic review of AI in precision medicine, without addressing cohort size or performance inflation."
    -> Neither source discusses small cohorts relative to model complexity or inflated performance, especially in genomics.

  X UNSUPPORTED:
    Claim: "Models trained on single-institution data often underperform on external datasets."
    Source says: "Source 3 discusses generalization from UK to USA, and Source 4 mentions methodological heterogeneity restricting generalizability, but neither directly addresses the claim."
    -> The source texts discuss AI performance in breast cancer screening and prostate cancer detection, but do not mention training on single-institution data or underperformance on external datasets.

  X UNCITED:
    Claim: "Few AI-based cancer screening tools have achieved broad clinical approval."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNSUPPORTED:
    Claim: "False-positive rates in CT lung nodule detection and mammography remain clinically significant."
    Source says: "For CT: 'specificity remained variable'; for mammography: no mention of false-positive rates."
    -> The source for CT lung nodule detection mentions variable specificity but does not state that false-positive rates are clinically significant, and the mammography source does not discuss false-positive rates.

  X UNSUPPORTED:
    Claim: "Tissue-of-origin misclassification in MCED tests is a key barrier to clinical deployment."
    Source says: "The abstract lists 'major factors which are preventing clinical implementation' but does not specify tissue-of-origin misclassification."
    -> The source does not mention tissue-of-origin misclassification as a barrier; it only notes that large-scale clinical validation studies are lacking.

  X UNSUPPORTED:
    Claim: "Requiring paired, synchronized data from multiple modalities reduces available training datasets and complicates real-world deployment."
    Source says: "Both abstracts focus on the benefits and performance of multimodal fusion, with no mention of data pairing limitations or deployment challenges."
    -> Neither source discusses any reduction in available training datasets or complications in real-world deployment caused by requiring paired, synchronized multimodal data.

  X UNCITED:
    Claim: "Large-scale pre-trained vision transformers such as CONCH and UNI are trained on millions of pathology images and enable zero-shot and few-shot cancer detection."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNCITED:
    Claim: "Federated learning enables training on distributed hospital datasets without sharing raw patient data."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  X UNSUPPORTED:
    Claim: "The NHS-Galleri trial in the UK is evaluating blood-based MCED tests in population screening contexts."
    Source says: "The abstract discusses MCED tests generally and notes that large-scale clinical validation studies are still lacking, but does not reference any specific trial."
    -> The source text does not mention the NHS-Galleri trial or any specific UK trial evaluating blood-based MCED tests in population screening contexts.

  X UNSUPPORTED:
    Claim: "SHAP values, GradCAM, and attention visualization are increasingly integrated into cancer detection pipelines."
    Source says: "Grad-CAM and SHAP techniques validate salient radiomic features; no mention of attention visualization or increasing integration."
    -> The source describes a single study using SHAP and Grad-CAM but does not mention attention visualization or state that these methods are increasingly integrated into cancer detection pipelines.

  X UNCITED:
    Claim: "Post-market surveillance of FDA-cleared AI tools in mammography and lung CT screening is generating real-world performance data."
    Citation: none attached
    -> Specific factual claim has no citation, so it cannot be grounded in the report's evidence trail.

  Supported examples:
    - Claim: "Large-scale deployment studies and head-to-head comparisons with radiologists have been reported, particularly in breast and lung cancer screening."
      Source says: "Source 2: 'This systematic review compares the diagnostic accuracy... of AI algorithms and radiologists in identifying lung nodules'; Source 3: 'an AI system... outperformed all of the human readers'."
      Reason: Source 2 is a systematic review comparing AI and radiologists for lung nodule detection, and Source 3 evaluates an AI system for breast cancer screening that outperforms radiologists, directly supporting the claim of head-to-head comparisons in both cancer types.
    - Claim: "Breast cancer detection using mammography plus ultrasound multimodal imaging with deep learning fusion achieved an AUC of 0.968."
      Source says: "AUC (0.968 (95% CI:0.947-0.989))"
      Reason: The source explicitly states that the multimodal classification model achieved an AUC of 0.968 (95% CI:0.947-0.989), which matches the claim.
    - Claim: "Breast cancer detection using mammography plus ultrasound multimodal imaging with deep learning fusion achieved a specificity of 96.41%."
      Source says: "Experimental results demonstrate that the multimodal classification model outperforms single-modal models in terms of specificity (96.41% (95% CI:93.10%-99.72%))"
      Reason: The source explicitly states that the multimodal classification model achieved a specificity of 96.41%.


=====================================================================
CUMULATIVE METRICS SUMMARY
=====================================================================
Stage 1: Intent Coverage .............................. Skipped
Stage 2: Directional Alignment ........................ Skipped
Stage 2: Data Extraction Accuracy ..................... Skipped/No Table
Stage 2: Synthesis Faithfulness ....................... Skipped/No Table
Stage 3: Claim Reliability ........................... 32.7%
Stage 3: Cited Grounding Rate ......................... 66.0%
=====================================================================
