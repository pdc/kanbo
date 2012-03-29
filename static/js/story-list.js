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
            if (storyIDs.indexOf(droppedID) >= 0) {
                var form$ = $(this).parent().find('form');
                $('input[name=order]', form$).val(storyIDs.join(' '));
                $('input[name=dropped]', form$).val(droppedID);
            }
        }
    })
    .disableSelection();
});