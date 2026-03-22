/**
 * Export Manager for Kisan Smart
 * Handles CSV and PDF exports of prediction history
 */

const ExportManager = {
    /**
     * Export predictions to CSV
     */
    exportToCSV(predictions, filename = null) {
        if (!predictions || predictions.length === 0) {
            Toast.warning('No predictions to export');
            return;
        }

        // Define headers
        const headers = [
            'Date',
            'Crop Type',
            'Farm Area (ha)',
            'Nitrogen (kg/ha)',
            'Phosphorus (kg/ha)',
            'Potassium (kg/ha)',
            'Soil pH',
            'Moisture (%)',
            'Temperature (°C)',
            'Fertilizer Type',
            'Quantity (kg/ha)',
            'Overall Confidence (%)'
        ];

        // Convert data to CSV rows
        const rows = predictions.map(pred => [
            new Date(pred.created_at).toLocaleString(),
            pred.crop_type || '',
            pred.farm_area || '',
            pred.nitrogen || '',
            pred.phosphorus || '',
            pred.potassium || '',
            pred.ph || '',
            pred.moisture || '',
            pred.temperature || '',
            pred.fertilizer_type || '',
            pred.quantity || '',
            Math.round(pred.overall_confidence || 0)
        ]);

        // Combine headers and rows
        const csvContent = [
            headers.join(','),
            ...rows.map(row => row.map(cell =>
                this.escapeCSV(cell)
            ).join(','))
        ].join('\n');

        // Create and trigger download
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);

        const defaultFilename = `predictions_export_${new Date().toISOString().split('T')[0]}.csv`;
        link.setAttribute('href', url);
        link.setAttribute('download', filename || defaultFilename);
        link.style.visibility = 'hidden';

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        Toast.success('CSV export downloaded successfully!');
    },

    /**
     * Export predictions to PDF
     */
    exportToPDF(predictions, filename = null) {
        if (!predictions || predictions.length === 0) {
            Toast.warning('No predictions to export');
            return;
        }

        try {
            const { jsPDF } = window.jspdf;
            const doc = new jsPDF();

            // Header
            doc.setFontSize(20);
            doc.setTextColor(40, 167, 69); // Green
            doc.text('Kisan Smart', 14, 20);

            doc.setFontSize(16);
            doc.setTextColor(0, 0, 0);
            doc.text('Prediction History Report', 14, 30);

            doc.setFontSize(10);
            doc.setTextColor(128, 128, 128); // Gray
            doc.text(`Generated on: ${new Date().toLocaleString()}`, 14, 38);
            doc.text(`Total Predictions: ${predictions.length}`, 14, 44);

            // Summary statistics
            doc.setFontSize(12);
            doc.setTextColor(0, 0, 0);
            doc.text('Summary', 14, 54);

            const avgConfidence = predictions.reduce((sum, p) => sum + (p.overall_confidence || 0), 0) / predictions.length;
            const uniqueCrops = new Set(predictions.map(p => p.crop_type)).size;

            doc.setFontSize(10);
            doc.text(`Average Confidence: ${avgConfidence.toFixed(1)}%`, 14, 62);
            doc.text(`Unique Crops: ${uniqueCrops}`, 14, 68);

            // Table
            const tableData = predictions.map(pred => [
                new Date(pred.created_at).toLocaleDateString(),
                pred.crop_type || 'N/A',
                pred.fertilizer_type || 'N/A',
                (pred.quantity || 0).toFixed(1),
                Math.round(pred.overall_confidence || 0) + '%'
            ]);

            doc.autoTable({
                startY: 76,
                head: [['Date', 'Crop', 'Fertilizer', 'Quantity (kg/ha)', 'Confidence']],
                body: tableData,
                theme: 'grid',
                styles: {
                    fontSize: 9,
                    cellPadding: 3
                },
                headStyles: {
                    fillColor: [40, 167, 69], // Green
                    textColor: [255, 255, 255],
                    fontStyle: 'bold'
                },
                alternateRowStyles: {
                    fillColor: [245, 245, 245]
                },
                margin: { top: 76 }
            });

            // Footer
            const pageCount = doc.internal.getNumberOfPages();
            for (let i = 1; i <= pageCount; i++) {
                doc.setPage(i);
                doc.setFontSize(8);
                doc.setTextColor(128, 128, 128);
                doc.text(
                    `Page ${i} of ${pageCount}`,
                    doc.internal.pageSize.getWidth() / 2,
                    doc.internal.pageSize.getHeight() - 10,
                    { align: 'center' }
                );
            }

            // Save
            const defaultFilename = `prediction_report_${new Date().toISOString().split('T')[0]}.pdf`;
            doc.save(filename || defaultFilename);

            Toast.success('PDF export downloaded successfully!');

        } catch (error) {
            console.error('PDF export failed:', error);
            Toast.error('Failed to generate PDF. Please try again.');
        }
    },

    /**
     * Escape CSV cell content
     */
    escapeCSV(cell) {
        const str = String(cell);

        // If contains comma, newline, or quote, wrap in quotes and escape quotes
        if (str.includes(',') || str.includes('\n') || str.includes('"')) {
            return `"${str.replace(/"/g, '""')}"`;
        }

        return str;
    }
};
