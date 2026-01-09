#!/usr/bin/env python3
"""
Test to verify external citations are actually in the article text
"""

import re


def test_external_citations():
    """Test that all external citations [37]-[56] appear in the article text."""
    
    print("="*70)
    print("TESTING EXTERNAL CITATIONS IN ARTICLE TEXT")
    print("="*70)
    
    # The article text from Step 4 output
    article_text = """Video Inpainting and Restoration: Diffusion Models for Repairing Missing or Corrupted Video Segments
Abstract
Video inpainting and restoration are critical processes in post-production workflows, aimed at repairing missing or corrupted video segments to improve overall video quality. Traditional methods often struggle with maintaining temporal consistency across frames, leading to artifacts and visual disruptions. Recent advancements have focused on leveraging diffusion models, which are well-suited for dealing with the temporal dynamics of video data. These models, including multi-scale feature modules and attention mechanisms, offer improved visual coherence and scene structure preservation. A key contribution of this paper is the integration of a temporal-aware approach that enhances video continuity by using spatial-temporal attention mechanisms. Our approach is quantitatively assessed using a synthetic dataset, demonstrating significant improvements in metrics such as Peak Signal-to-Noise Ratio (PSNR) and Structural Similarity Index (SSIM), compared to traditional methods. For instance, the PSNR improvement is observed to be \\left(3.5\\ \\text{dB}\\right) higher than baseline methods. The findings underscore the potential of diffusion-based techniques to advance video restoration tasks, suggesting future applications in more complex video editing scenarios.

1. Introduction
Video inpainting and restoration have emerged as significant research domains within computer vision, primarily focusing on the repair and enhancement of video sequences that contain missing or corrupted segments. These processes are crucial in post-production workflows, where maintaining the quality and continuity of video content is paramount [1], [2]. Video inpainting involves reconstructing lost or damaged parts of a video, ensuring temporal and spatial consistency, which presents a formidable challenge due to the complex dynamics and motion inherent in video data [1], [3]. Despite the advancements in video processing techniques, existing methods often face limitations, particularly in achieving temporal consistency across frames. Traditional approaches frequently rely on adjacent frames to reconstruct the missing data, which can result in artifacts and visual inconsistencies, especially in the presence of complex motion [4]. This issue underscores a significant research gap in developing robust models that can effectively handle such complexities [5], [6]. The introduction of diffusion models has shown promise in addressing these challenges by leveraging their inherent ability to model temporal dependencies and interpolate missing data with high fidelity [7], [8]. Current state-of-the-art methods in video inpainting utilize various deep learning architectures, including convolutional neural networks (CNNs) and generative adversarial networks (GANs), to enhance visual quality and continuity [9]. However, these methods often struggle with maintaining temporal coherence across frames, particularly under conditions of fast or erratic motion [10]. The recent advancement of diffusion models offers a novel solution, as they are capable of capturing intricate temporal dynamics and generating high-quality interpolations by modeling the probabilistic distribution of the video sequences [11], [12]. This synthesis aims to explore the application of diffusion models in video inpainting and restoration, highlighting their advantages in preserving temporal consistency and improving visual quality. The paper examines the temporal-aware approach of diffusion models, which integrates spatial-temporal attention mechanisms to achieve superior inpainting results [13], [14]. The key contribution of this work is to demonstrate how these models can be effectively utilized to address the limitations of existing techniques, thereby enhancing post-production workflows [15], [16]. The remainder of the paper is structured as follows: Section II provides a detailed overview of the existing methodologies in video inpainting and restoration, focusing on their strengths and limitations. In Section III, we delve into the architecture of diffusion models, discussing their applicability and effectiveness in video restoration tasks. Section IV presents experimental results, showcasing the improvements in video quality achieved by the proposed approach. A synthetic results table is provided below to illustrate the comparative performance of our diffusion model against traditional methods:

Method	Temporal Consistency	Visual Quality	Processing Time (s)
CNN-based	Moderate	High	0. 45
GAN-based	Low	Moderate	0. 60
Diffusion Model	High	High	0. 75
Finally, Section V concludes the paper with a discussion on future research directions and potential applications of diffusion models in broader video processing contexts [17], [18], [19]. This work not only advances the field of video restoration but also sets a foundation for further exploration into diffusion-based frameworks for various video enhancement tasks [20], [21].

2. Background and Related Work
The field of video inpainting and restoration has undergone significant evolution, transitioning from early heuristic-based methods to sophisticated deep learning techniques. Historically, video inpainting involved manual frame editing or using simple interpolation techniques, which were often inadequate for maintaining temporal consistency across frames [1], [2]. As computational capabilities expanded, more advanced algorithms emerged, such as those leveraging global affine transformations. However, these approaches were limited by inaccurate reconstructions in dynamic scenes due to their assumption of global motion [3].

The introduction of diffusion models marked a pivotal advancement in this domain. Diffusion models, particularly their application to video inpainting, are designed to model the gradual transformation of noise to a coherent image, thereby facilitating high-quality restorations [4]. These models, often denoted as 
q
(
x
t
∣
x
t
−
1
)
,
d
e
p
i
c
t
a
p
r
o
c
e
s
s
w
h
e
r
e
q(x 
t
​
 ∣x 
t−1
​
 ),depictaprocesswhere\\mathbf{x}t
r
e
p
r
e
s
e
n
t
s
t
h
e
v
i
d
e
o
f
r
a
m
e
a
t
t
i
m
e
representsthevideoframeattimet
c
o
n
d
i
t
i
o
n
e
d
o
n
f
r
a
m
e
conditionedonframe\\mathbf{x}{t-1}$ [5]. This probabilistic framework allows for the incorporation of temporal dynamics, which is essential for maintaining visual coherence across frames [6], [7].

Seminal contributions in this area include the development of multi-scale feature modules combined with attention mechanisms, such as the MFMAM approach. This method significantly enhances image completion by leveraging multi-scale features to capture fine details while maintaining the overall scene structure [8], [9]. Another notable work is StoryDiffusion, which utilizes a self-attention mechanism aimed at generating long-range image and video sequences, ensuring temporal consistency and reducing artifacts [10], [11].

The current research landscape is vibrant, with numerous models being proposed for various video restoration tasks. For instance, 4EV integrates text-to-image diffusion models with temporal dynamics to address text-to-video synthesis challenges [12]. This model exemplifies the trend towards integrating spatial-temporal attention mechanisms to preserve motion consistency in video frames [13]. Moreover, the integration of advanced prior knowledge, such as physical sensor models, has been suggested to enhance restoration quality further [14].

Despite these advancements, several research gaps remain unaddressed. Many existing approaches still struggle with ensuring temporal consistency across video frames, leading to flickering and instability, especially in complex motion scenarios [15], [16]. Additionally, there is a need for models that can handle diverse degradation types, such as motion blur and atmospheric turbulence, which are common in real-world video capture [17], [18].

Recent efforts have also focused on overcoming the inefficiencies of traditional diffusion models in solving inverse problems. The Come-Closer-Diffuse-Faster (CCDF) methodology exemplifies this by accelerating the diffusion process, which is crucial for real-time applications [19], [20]. Moreover, the inclusion of uncertainty quantification methods is becoming increasingly important to provide confidence estimates in critical applications, such as medical imaging [21], [22].

In summary, while diffusion models have significantly enhanced video inpainting and restoration capabilities, there is ongoing research to improve their efficiency, robustness, and applicability to a wider range of degradation scenarios. This paper aims to address these gaps by proposing a novel temporal-aware diffusion model that optimizes video quality in post-production workflows, thereby advancing the state of the art in video restoration [23], [24], [25].

Model	Key Feature	Performance Metric
MFMAM	Multi-scale feature module	Improved image completion
StoryDiffusion	Self-attention for long-range sequences	Reduced artifacts
4EV	Text-to-video synthesis integration	Enhanced motion consistency
CCDF	Accelerated diffusion process	Faster real-time applications
The synthesis presented here will contribute to the literature by integrating these insights into a cohesive framework for video inpainting, addressing both temporal consistency and computational efficiency [26], [27], [28], [29], [30]. The proposed approach will leverage the strengths of both traditional and modern diffusion models, setting a new benchmark for video restoration methodologies [31], [32], [33], [34], [35].

3. Methodology and Approach
Overview of Methodological Frameworks
The development of video inpainting and restoration techniques has increasingly leveraged the power of diffusion models, which have shown significant promise in addressing the challenges associated with reconstructing missing or corrupted video segments [1], [22]. These models work by modeling the distribution of observed data through a series of iterative denoising steps, which are particularly effective in temporal and spatial video editing applications [22]. The proposed framework integrates temporal-aware diffusion models that utilize spatial-temporal attention mechanisms to maintain motion consistency across frames [22].

Detailed Description of Techniques and Algorithms
Diffusion models employed for video inpainting are typically based on a probabilistic framework, where the process involves both forward and reverse diffusion steps. The forward process gradually adds noise to the video frames, while the reverse process aims to reconstruct the original data by removing this noise [4], [32]. The mathematical foundation of these models can be expressed in terms of a forward diffusion process 
q
(
x
t
∣
x
t
−
1
)
a
n
d
a
r
e
v
e
r
s
e
p
r
o
c
e
s
s
q(x 
t
​
 ∣x 
t−1
​
 )andareverseprocessp_{\\theta}\\left(\\mathbf{x}{t-1} \\mid \\mathbf{x}{t}\\right), where 
\\theta
\\theta represents model parameters optimized during training.

Incorporating attention mechanisms, such as the multi-scale feature module with self-attention, enhances the model's ability to capture long-range dependencies and maintain visual coherence [9]. Techniques like MotionDirector and Trailblazer facilitate the handling of complex video manipulations by providing essential motion cues that guide the inpainting process [22].

Comparison of Approaches with Strengths/Weaknesses
Diffusion-based methods exhibit several advantages over traditional video inpainting techniques. For instance, they are less susceptible to the artifacts and inconsistencies that often arise when handling complex motion in videos [1]. However, these models require significant computational resources due to the iterative nature of the denoising process [32]. Moreover, while diffusion models excel in maintaining temporal consistency, their performance heavily relies on the quality and diversity of training data [4].

Comparative studies with other deep learning approaches, such as U-Net and its variants, have shown that diffusion models generally outperform in terms of precision and output quality, albeit at the cost of increased computational demands [4], [14].

Evaluation Metrics and Validation Methods
The evaluation of diffusion-based video inpainting models employs various quantitative metrics, including Peak Signal-to-Noise Ratio (PSNR), Structural Similarity Index (SSIM), and Mean Squared Error (MSE) [34]. These metrics provide insights into the visual quality and fidelity of the reconstructed video segments. Additionally, qualitative assessments through human testing are crucial for evaluating subjective video quality enhancements [21].

Validation of the proposed methodologies is typically conducted using a combination of synthetic datasets and real-world benchmarks. These datasets are curated to include diverse video scenarios, ensuring that the models are robust and generalize well across different video content [22].

Datasets, Benchmarks, and Experimental Setups
The experimental setup for evaluating video inpainting techniques often involves datasets like the DAVIS and YouTube-VOS, which provide a wide range of video sequences with annotated inpainting masks [14], [22]. The models are trained on these datasets, using data augmentation techniques to enhance their robustness [22].

For benchmarking, the models are tested against state-of-the-art baselines, allowing for a direct comparison of performance metrics [4], [14]. A typical experimental setup involves partitioning the dataset into training and validation sets, ensuring that the validation data is representative of unseen video content [14].

Synthetic Results Table
To illustrate the effectiveness of different methodologies, a synthetic results table comparing key performance metrics across various models is presented below.

Model	PSNR (dB)	SSIM	MSE
Diffusion Model A	34.56	0.945	0.0021
Traditional U-Net	32.78	0.910	0.0035
MotionDirector	35.12	0.952	0.0019
Table 1: Synthetic performance comparison of video inpainting models.

In summary, diffusion models offer a robust framework for video inpainting and restoration, effectively addressing the challenges of maintaining temporal consistency and visual quality. While they present computational challenges, their integration with advanced attention mechanisms and probabilistic frameworks positions them as a powerful tool in video post-production workflows [1], [9], [22].

4. Results and Key Findings
4.1 Primary Contributions
The diffusion-based video inpainting model demonstrated significant improvements in both quantitative and qualitative metrics when compared to traditional methods. In terms of quantitative analysis, the model achieved a peak signal-to-noise ratio (PSNR) of 35.4 dB and a structural similarity index measure (SSIM) of 0.95 on the TaichiHD dataset, outperforming previous state-of-the-art models by 12% and 8% respectively [30]. These metrics indicate a substantial enhancement in video quality, with improved preservation of fine details and reduced noise artifacts.

Qualitatively, the restored videos exhibited a high degree of temporal consistency, a critical aspect in video restoration that is often compromised in conventional approaches [1]. Visual inspection revealed that the model's ability to maintain temporal coherence across frames was significantly better, reducing the occurrence of flickering and motion artifacts commonly seen in competitive models [34]. The use of spatial-temporal attention mechanisms allowed the model to adaptively manage the varied dynamics of motion paths, ensuring smooth transitions across frames [22].

The model's architecture leverages advanced diffusion processes that incorporate temporal awareness, which is crucial for handling complex motion sequences. The integration of multi-scale feature modules and attention mechanisms further enhanced the model's capacity to manage variable motion dynamics, achieving seamless inpainting results [9]. This approach not only improved the visual coherence of the inpainted segments but also ensured that the restored content was contextually relevant and visually appealing.

4.2 Supporting Evidence
A comparative analysis across various studies underscores the model's superiority in video inpainting tasks. The diffusion-based approach was validated against other models such as MotionDirector and Text2LIVE, where it consistently produced higher fidelity results [22]. In particular, when tested on the standard PU-1K and PU-GAN benchmarks, the model achieved significantly lower Chamfer and Hausdorff distances, indicative of its enhanced geometrical accuracy and reduced distortion [2].

The statistical significance of these improvements was confirmed through rigorous testing, with p-values less than 0.01, indicating that the improvements were not due to random chance [23]. Furthermore, the model's effectiveness was validated using a variety of datasets, including real-world video footage, which highlighted its robustness and applicability across diverse scenarios [30].

The model's capacity for high-fidelity restoration was particularly evident in scenarios involving complex motion. The temporal-aware approach enabled the model to predict and correct for motion-induced artifacts with remarkable precision, far surpassing the capabilities of previous methods that often falter in such conditions [32]. The ability to handle abrupt changes in motion paths without degrading visual quality is a testament to the model's advanced design principles and its potential for widespread application in video post-production workflows.

4.3 Limitations
Despite the substantial advancements, the model has certain limitations that warrant further investigation. One notable limitation is its computational complexity. The diffusion process, while effective, is resource-intensive and may not be suitable for real-time applications without significant optimization [36]. The current implementation demands high computational power, which could limit its accessibility in environments with constrained resources.

Moreover, while the model performs exceptionally well on datasets with well-defined motion patterns, its performance on more chaotic or unpredictable motion sequences is comparatively less robust. This limitation suggests that the model's ability to generalize across all types of motion is not yet fully realized, and future work should focus on enhancing its adaptability to diverse motion scenarios [1].

Another area for improvement is the model's handling of extreme lighting conditions and occlusions. While it manages these challenges better than existing models, there is still room for improvement in scenarios with extensive occlusions or highly dynamic lighting, where the model occasionally produces suboptimal inpainting results [9]. Future research should aim to integrate advanced prior knowledge, such as physical sensor models, to further enhance restoration quality in these challenging conditions [36].

In conclusion, while the diffusion-based video inpainting model presents a significant leap forward in the field of video restoration, it also highlights areas for future research and development. By addressing these limitations, the model's applicability and performance can be further enhanced, paving the way for even more advanced solutions in video post-production and restoration workflows.

5. Discussion and Analysis
The advancement of video inpainting and restoration through diffusion models represents a significant stride in multimedia processing, particularly in the context of repairing missing or corrupted video segments. This section synthesizes findings across various studies, evaluates conflicting results, and explores the theoretical and practical ramifications of these advancements.

5.1 Comparative Analysis
The integration of diffusion models in video inpainting has been explored through various frameworks, each contributing distinct methodologies and outcomes. Notably, the 4EV model leverages the combination of text-to-image diffusion with spatial-temporal dynamics to enhance video editing capabilities [22]. This approach contrasts with traditional methods, which often rely on global affine transformations and exhibit limitations in preserving temporal consistency during complex motion scenarios [1].

Diffusion models have shown superiority in several domains, including super-resolution tasks, where they have outperformed conventional statistical and patch-based approaches [14]. The innovative use of multi-scale features and attention mechanisms, as demonstrated in MFMAM and StoryDiffusion, further enhances the quality of image and video completion by preserving scene structure and visual coherence [9].

However, conflicting findings arise regarding the effectiveness of these models in maintaining temporal consistency. While some models have achieved high-quality video generation with minimal data, others report challenges with artifacts and inconsistencies [1], [36]. The CRAFF module, for example, has been critiqued for its tendency to overfit reference frames, leading to temporal inconsistencies [34].

5.2 Theoretical Implications
The theoretical implications of employing diffusion models in video restoration are profound. At the core, these models facilitate a probabilistic framework that can be elegantly described by the equation:

q
(
x
t
∣
x
t
−
1
)
=
N
(
x
t
;
α
t
x
t
−
1
,
(
1
−
α
t
)
I
)
q(x 
t
​
 ∣x 
t−1
​
 )=N(x 
t
​
 ; 
α 
t
​
 
​
 x 
t−1
​
 ,(1−α 
t
​
 )I)

Such a framework allows for precise modeling of the temporal evolution of video frames, capturing both spatial and temporal dependencies. This probabilistic approach aligns with the findings of several studies that emphasize the importance of incorporating advanced prior knowledge and uncertainty quantification to enhance restoration quality [36].

Furthermore, the application of diffusion models in video analysis introduces a paradigm shift in how visual data is processed. The capacity to generate high-fidelity outputs with minimal training data suggests a potential reduction in the computational resources required for model training, aligning with the trends seen in other deep learning applications [22].

5.3 Practical Applications
The practical applications of diffusion models in video inpainting and restoration are extensive and impactful. In post-production workflows, these models enable the seamless repair of video segments that are either missing or corrupted, significantly enhancing the visual quality and continuity of multimedia outputs [1]. This capability is crucial in industries such as film and gaming, where visual fidelity is paramount.

Moreover, the adaptation of diffusion models in specialized areas such as motion-artifact correction has demonstrated promising results, with studies highlighting the model's ability to handle complex degradations like motion blur and atmospheric turbulence [32], [36]. The practical utility of such applications is underscored by their potential to improve video-based deep learning applications, as seen in AutoFoley's audio-visual synthesis and MEMC-Net's enhancement of visual quality [21].

A synthetic results table can illustrate the comparative performance of various models:

Model	Temporal Consistency	Visual Quality	Computational Efficiency
4EV	High	Excellent	Moderate
MFMAM	Moderate	Good	High
CRAFF	Low	Fair	Low
StoryDiffusion	High	Excellent	Moderate
Table 1: Synthetic comparison of model performance across key metrics.

In conclusion, diffusion models are poised to redefine the landscape of video inpainting and restoration, offering both theoretical insights and practical benefits. Future research may further explore the integration of these models with other advanced technologies, potentially leading to even more robust and efficient video processing solutions [4], [14], [36].

6. Future Research Directions
The field of video inpainting and restoration using diffusion models is ripe for further exploration, with several open challenges and promising research directions. One significant challenge is the integration of advanced prior knowledge, such as physical sensor models, to enhance the restoration quality of video segments. This integration could potentially improve the reliability of reconstructed frames, especially in scenarios where sensor data can provide additional context for the missing or corrupted segments [36].

A promising research direction lies in extending current frameworks to handle a broader range of video degradation types, including motion blur and atmospheric turbulence. Addressing these issues requires sophisticated models that can adaptively manage varying degrees of degradation while maintaining temporal consistency across frames. Such advancements would likely require the development of more robust temporal dynamics models that could be inspired by recent successes in text-to-video synthesis [1], [22].

Methodologically, one area that warrants further investigation is the quantification of uncertainty in video inpainting models. Developing methods to provide confidence estimates for the reconstructed video frames can be crucial for applications that require high reliability, such as medical imaging and surveillance. This can be achieved by incorporating probabilistic models that assess the likelihood of various reconstruction outcomes, thus enabling the generation of more confident predictions [36].

Emerging applications of diffusion models in video inpainting include their use in enhancing video quality for post-production workflows in the film and entertainment industry. These models can be leveraged to improve video continuity and visual quality, thereby reducing the time and cost associated with manual post-production editing [1], [9]. Moreover, the development of models that can handle complex motion patterns and scene dynamics might lead to improved techniques for automated video editing and synthesis [22].

Cross-disciplinary opportunities are abundant, particularly in combining insights from computational photography, computer vision, and machine learning. For instance, the development of multi-scale networks that preserve scene structure and visual coherence could benefit from advances in both image inpainting and video synthesis [9]. Additionally, the integration of spatial-temporal attention mechanisms could further enhance the ability of models to deal with motion inconsistencies and artifacts, thus broadening the applicability of these techniques across different domains [22].

To facilitate these advancements, a synthetic results table illustrating potential improvements in restored video quality using different diffusion model architectures could be instrumental. The following table provides a hypothetical comparison of video quality metrics using various diffusion model enhancements:

Model Type	PSNR (dB)	SSIM	Temporal Consistency
Baseline Model	28.5	0.85	Low
Advanced Model 1	32.1	0.89	Medium
Advanced Model 2	34.7	0.92	High
This synthetic table demonstrates how methodological improvements in diffusion models might translate into tangible enhancements in video quality metrics. Further research is needed to validate these potential improvements across diverse datasets and real-world scenarios.

7. Conclusion
The exploration of diffusion models for video inpainting and restoration has provided significant insights into their capability to repair and enhance video quality, particularly in post-production workflows. Our synthesis of the literature reveals that diffusion-based techniques excel in maintaining temporal consistency and visual coherence, which are critical for achieving seamless video restoration [1], [9]. Unlike traditional methods that often falter under complex motion scenarios, diffusion models leverage advanced temporal-aware mechanisms to mitigate such challenges [1], [32].

The current state of the field demonstrates a robust movement towards integrating diffusion models with multi-scale and attention-based architectures, enhancing their ability to address video degradation effectively [9], [22]. These models offer a compelling alternative to conventional techniques by utilizing probabilistic methods that allow for more nuanced and accurate inpainting results. The integration of spatial-temporal attention mechanisms has shown to preserve motion consistency, which is pivotal for high-fidelity video editing [22].

Key takeaways for researchers and practitioners include the effectiveness of diffusion models in enhancing video quality and the potential to further develop these models to handle a broader range of degradation types, such as motion blur and atmospheric disturbances [36]. These advancements suggest that future work should focus on expanding the capabilities of diffusion models to encompass a wider spectrum of video restoration challenges, potentially incorporating physical sensor models to further elevate restoration quality [36].

In conclusion, the trajectory of diffusion models in video inpainting and restoration appears promising, with their impact being increasingly felt in both academic and practical domains. As these models continue to evolve, they are expected to redefine standards in video quality enhancement, offering refined tools for post-production workflows. The continued development and integration of advanced algorithms will likely drive further improvements in restoration quality, ensuring these techniques remain at the forefront of video processing technology.

Model	Temporal Consistency	Visual Coherence	Degradation Types Handled
Traditional	Moderate	Moderate	Limited
Diffusion-Based	High	High	Broad
Table 1 illustrates a synthetic comparison between traditional and diffusion-based models, highlighting the advantages of the latter in handling a wider array of degradation types with superior temporal consistency and visual coherence. This comparison underscores the importance of continued exploration and adaptation of diffusion models to meet the evolving demands of video restoration [9], [36]."""
    
    # Extract all citations from the article
    all_citations = set(re.findall(r'\[(\d+)\]', article_text))
    
    # Expected external citations [37]-[56]
    expected_external = set(str(i) for i in range(37, 57))
    
    print("\n📊 ANALYSIS RESULTS:")
    print("-" * 70)
    print(f"Total citations found in article: {len(all_citations)}")
    print(f"Citation range: {min(all_citations)} to {max(all_citations)}")
    
    print("\n🔍 CHECKING EXTERNAL CITATIONS [37]-[56]:")
    external_found = all_citations & expected_external
    external_missing = expected_external - all_citations
    
    print(f"  External citations in text: {len(external_found)}/20")
    print(f"  Present: {sorted(external_found)}")
    print(f"  Missing: {sorted(external_missing)}")
    
    # Check if all citations [1]-[56] are present
    expected_all = set(str(i) for i in range(1, 57))
    all_present = all_citations == expected_all
    
    print("\n✅ VERIFICATION:")
    print(f"  All citations [1]-[56] in text: {all_present}")
    
    if external_missing:
        print("\n❌ ISSUE CONFIRMED:")
        print("  External citations [37]-[56] are NOT in the article text!")
        print("  They only appear in the reference list at the bottom.")
        print("\n  This means the integration in Step 2.9 failed or the")
        print("  fallback logic is not working properly.")
    else:
        print("\n✅ SUCCESS:")
        print("  All external citations [37]-[56] are in the article text!")
        print("  The integration is working correctly.")
    
    print("\n" + "="*70)
    
    # Show which sections contain external citations
    if external_found:
        print("\n📍 SECTIONS WITH EXTERNAL CITATIONS:")
        sections = article_text.split('\n\n')
        for i, section in enumerate(sections[:10]):  # Check first 10 sections
            section_citations = set(re.findall(r'\[(\d+)\]', section))
            section_external = section_citations & expected_external
            if section_external:
                # Get section title
                lines = section.split('\n')
                title = lines[0] if lines else f"Section {i+1}"
                print(f"  {title}: {sorted(section_external)}")
    
    return len(external_missing) == 0


if __name__ == "__main__":
    success = test_external_citations()
    exit(0 if success else 1)
