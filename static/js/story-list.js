// Make the stories be sortable.

$(function () {
    $('.story-bin').sortable({
        connectWith: '.story-bin',
        update: function (event, ui) {
            var droppedID = ui.item.attr('id').replace(/^story-/, '');
            var eltIDs = $(this).sortable('toArray');
            var storyIDs = [];
            for (var i = 0; i < eltIDs.length; ++i) {
                storyIDs.push(eltIDs[i].replace(/^story-/, ''));
            }
            var droppedIndex = storyIDs.indexOf(droppedID);
            if (droppedIndex >= 0) {
                var succID = (droppedIndex + 1 < storyIDs.length ? storyIDs[droppedIndex + 1] : '-');
                var abbreviatedIDs = [droppedID, succID];

                var ajaxEnabled = $('#ajaxEnabled:checked').length;
                if (ajaxEnabled) {
                    var url = $(this).parent().attr('data-ajax-url');
                    $.ajax(url, {
                        type: 'POST',
                        dataType: 'json',
                        data: {
                            'order': abbreviatedIDs,
                            'dropped': droppedID,
                        }
                    });
                } else {
                    var form$ = $(this).parent().find('form');
                    $('input[name=order]', form$).val(abbreviatedIDs.join(' '));
                    $('input[name=dropped]', form$).val(droppedID);
                }
            }
        }
    })
    .disableSelection();
});