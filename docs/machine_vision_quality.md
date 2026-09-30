# Machine Vision for Quality Inspection

## Components
A machine vision system consists of an industrial camera, a lens, lighting, and software that analyses the images. Lighting is often the most important part: backlighting shows the outline of a part, while low-angle light makes scratches and dents visible.

## Classic image processing
Rule-based methods measure dimensions, count holes, read barcodes, or compare a part to a golden reference image. They work well when parts and lighting are very consistent.

## Deep learning inspection
Convolutional neural networks (CNNs) can learn to recognise defects such as cracks, stains or missing components from labelled example images. They handle natural variation better than fixed rules but need a good training dataset, including enough images of rare defects.

## Measuring performance
A false reject is a good part that is thrown away; a false accept is a defective part that reaches the customer. Tuning the system is a trade-off between these two errors, and the right balance depends on the cost of each mistake.
