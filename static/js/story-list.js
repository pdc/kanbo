// Make the stories be sortable.

$(function () {
    $('.story-bin').sortable({
        update: function (event, ui) {
            var eltIDs = $(this).sortable('toArray');
            var storyIDs = [];
            for (var i = 0; i < eltIDs.length; ++i) {
                storyIDs.push(eltIDs[i].replace(/^story-/, ''));
            }
            var form$ = $(this).next('form');
            $('input[name=order]', form$).val(storyIDs.join(' '));
        }
    });
    $('.story-bin').disableSelection();
});