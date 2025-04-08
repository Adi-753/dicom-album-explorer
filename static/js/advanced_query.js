$(document).ready(function() {
    // Add condition button
    $('#addCondition').click(function() {
        const conditionHtml = $('#queryConditions .condition').first().clone();
        conditionHtml.find('input[type="text"]').val('');
        conditionHtml.find('select').prop('selectedIndex', 0);
        $('#queryConditions').append(conditionHtml);
    });
    
    // Remove condition button
    $(document).on('click', '.remove-condition', function() {
        if ($('#queryConditions .condition').length > 1) {
            $(this).closest('.condition').remove();
        } else {
            alert('You must have at least one condition');
        }
    });
    
    $('#advancedQueryForm').on('submit', function(e) {
        e.preventDefault();
        
        const conditions = [];
        const joinOperator = $('input[name="joinOperator"]:checked').val();
        
        $('.condition').each(function() {
            const field = $(this).find('.query-field').val();
            const operator = $(this).find('.query-operator').val();
            const value = $(this).find('.query-value').val();
            
            if (field && value) {
                conditions.push({
                    field: field,
                    operator: operator,
                    value: value
                });
            }
        });
        
        if (conditions.length === 0) {
            alert('Please add at least one condition');
            return;
        }
        
        const queryData = {
            conditions: conditions,
            join_operator: joinOperator
        };
        
        $.ajax({
            url: '/query/advanced',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(queryData),
            success: function(response) {
                if (response.success) {
                    $('#resultsSection').show();
                    
                    $('#queryDescription').text(response.query);
                    
                    const tbody = $('#resultsTable tbody');
                    tbody.empty();
                    
                    $('#resultCount').text(`${response.result_count} results`);
                    
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
                        
                        $('#createAlbumBtn').prop('disabled', false);
                        
                        $('#queryJson').val(JSON.stringify(queryData));
                    } else {
                        tbody.append(`
                            <tr>
                                <td colspan="5" class="text-center">No results found</td>
                            </tr>
                        `);
                        
                        $('#createAlbumBtn').prop('disabled', true);
                    }
                } else {
                    alert('Error: ' + response.error);
                }
            },
            error: function(xhr) {
                alert('Error: ' + (xhr.responseJSON ? xhr.responseJSON.error : 'Query failed'));
            }
        });
    });
    
    $('#createAlbumBtn').click(function() {
        $('#createAlbumSection').show();
        $('html, body').animate({
            scrollTop: $('#createAlbumSection').offset().top
        }, 500);
    });
    
    $('#createAlbumForm').on('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        
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
    
    loadQueryHistory();
});

function loadQueryHistory() {
    $.getJSON('/query_history', function(response) {
        if (response.success && response.history) {
            const tbody = $('#historyTable tbody');
            tbody.empty();
            
            if (response.history.length === 0) {
                tbody.append(`
                    <tr>
                        <td colspan="4" class="text-center">No query history yet</td>
                    </tr>
                `);
                return;
            }
            
            response.history.forEach(function(item) {
                const date = new Date(item.executed_date).toLocaleString();
                
                tbody.append(`
                    <tr>
                        <td class="font-monospace">${item.query}</td>
                        <td>${date}</td>
                        <td>${item.result_count}</td>
                        <td>
                            <button class="btn btn-sm btn-primary rerun-query" 
                                    data-query='${JSON.stringify(item)}'>
                                Re-run
                            </button>
                        </td>
                    </tr>
                `);
            });
        }
    }).fail(function() {
        console.error('Failed to load query history');
    });
}
