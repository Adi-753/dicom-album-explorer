let currentQueryResults = null;
let currentQueryJson = null;

$(document).ready(function() {
    // File upload form
    $('#uploadForm').on('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const fileInput = $('#files')[0];
        
        if (fileInput.files.length === 0) {
            alert('Please select at least one file to upload');
            return;
        }
        
        for (let i = 0; i < fileInput.files.length; i++) {
            formData.append('files[]', fileInput.files[i]);
        }
        
        $.ajax({
            url: '/upload',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                if (response.success) {
                    fetchMetadata();
                    alert(response.message);
                } else {
                    alert('Error: ' + response.error);
                }
            },
            error: function(xhr) {
                alert('Error: ' + (xhr.responseJSON ? xhr.responseJSON.error : 'Failed to upload files'));
            }
        });
    });
    
    // Directory scan form
    $('#scanForm').on('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        
        $.ajax({
            url: '/scan',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                if (response.success) {
                    fetchMetadata();
                    alert(response.message);
                } else {
                    alert('Error: ' + response.error);
                }
            },
            error: function(xhr) {
                alert('Error: ' + (xhr.responseJSON ? xhr.responseJSON.error : 'Failed to scan directory'));
            }
        });
    });
    
    // query form
    $('#simpleQueryForm').on('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        
        $.ajax({
            url: '/query/simple',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                if (response.success) {
                    displayQueryResults(response);
                    
                    currentQueryResults = response.results;
                    currentQueryJson = JSON.stringify({
                        conditions: [{
                            field: formData.get('field'),
                            operator: formData.get('operator'),
                            value: formData.get('value')
                        }],
                        join_operator: 'AND'
                    });
                    
                    $('#queryJson').val(currentQueryJson);
                    $('#createAlbumBtn').prop('disabled', false);
                } else {
                    alert('Error: ' + response.error);
                }
            },
            error: function(xhr) {
                alert('Error: ' + (xhr.responseJSON ? xhr.responseJSON.error : 'Query failed'));
            }
        });
    });
    
    // Create album form
    $('#createAlbumForm').on('submit', function(e) {
        e.preventDefault();
        
        if (!currentQueryResults || currentQueryResults.length === 0) {
            alert('No query results to create album from');
            return;
        }
        
        const formData = new FormData(this);
        formData.append('query_json', currentQueryJson);
        
        $.ajax({
            url: '/create_album',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                if (response.success && response.redirect) {
                    window.location.href = response.redirect;
                } else {
                    alert('Error: ' + response.error);
                }
            },
            error: function(xhr) {
                alert('Error: ' + (xhr.responseJSON ? xhr.responseJSON.error : 'Failed to create album'));
            }
        });
    });
    
    // Album deletion
    $(document).on('click', '.delete-album', function() {
        if (confirm('Are you sure you want to delete this album? This action cannot be undone.')) {
            const albumId = $(this).data('album-id');
            
            $.ajax({
                url: `/album/${albumId}/delete`,
                type: 'POST',
                success: function(response) {
                    if (response.success && response.redirect) {
                        window.location.href = response.redirect;
                    } else {
                        alert('Error: ' + response.error);
                    }
                },
                error: function() {
                    alert('Failed to delete album');
                }
            });
        }
    });
});

// Fetch metadata for loaded DICOM files
function fetchMetadata() {
    $.getJSON('/metadata', function(response) {
        if (response.metadata_sample) {
            $('#dataSection').show();
            
            $('#fileCount').text(`${response.total_files} files loaded`);
            
            const tbody = $('#metadataTable tbody');
            tbody.empty();
            
            response.metadata_sample.forEach(function(item) {
                tbody.append(`
                    <tr>
                        <td>${item.PatientID || ''}</td>
                        <td>${item.PatientName || ''}</td>
                        <td>${item.Modality || ''}</td>
                        <td>${item.StudyDate || ''}</td>
                        <td>${item.SeriesDescription || ''}</td>
                    </tr>
                `);
            });
            
            const fieldSelect = $('#queryField');
            fieldSelect.empty();
            
            response.available_fields.forEach(function(field) {
                fieldSelect.append(`<option value="${field}">${field}</option>`);
            });
        }
    }).fail(function() {
        alert('Failed to fetch metadata');
    });
}

function displayQueryResults(response) {
    const tbody = $('#resultsTable tbody');
    tbody.empty();
    
    if (response.results && response.results.length > 0) {
        response.results.forEach(function(item) {
            tbody.append(`
                <tr>
                    <td>${item.PatientID || ''}</td>
                    <td>${item.PatientName || ''}</td>
                    <td>${item.Modality || ''}</td>
                    <td>${item.StudyDate || ''}</td>
                    <td>${item.SeriesDescription || ''}</td>
                </tr>
            `);
        });
    } else {
        tbody.append(`
            <tr>
                <td colspan="5" class="text-center">No results found</td>
            </tr>
        `);
    }
    
    $('#resultCount').text(`${response.result_count} results`);
}