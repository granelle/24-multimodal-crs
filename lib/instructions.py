def select_instruction(args):

    coi = 'CoI' in args.model_name
    domain = args.domain
    task = args.task

    if args.task == "description":
        instr = "Describe this image in detail, including its content, style, and vibe."

    elif task == "rec_title":
        
        if domain == 'music':
            
            if coi:
                instr = f"Given the request, provide recommendations. Think step by step. First understand the given image(s) in detail, including its content, style, and vibe. Then, think of music pieces that capture the essence of the image(s). Enumerate 20 music pieces (1., 2., ...) in the order of relevance. Each piece should take the Artist - Title format. Don't say anything else."
            else:
                instr = f"Given the request, provide recommendations. Enumerate 20 music pieces (1., 2., ...) in the order of relevance. Each piece should take the Artist - Title format. Don't say anything else."
                
        elif domain == 'books':
            
            if coi:
                instr = f"Given the request, provide recommendations. Think step by step. First understand the given image(s) in detail, including its content, style, and vibe. Then, think of books that capture the essence of the image(s). Enumerate 20 books (1., 2., ...) in the order of relevance. Each book should take the Author - Title format. Don't say anything else."
            else:
                instr = f"Given the request, provide recommendations. Enumerate 20 books (1., 2., ...) in the order of relevance. Each book should take the Author - Title format. Don't say anything else."

        else:
            raise ValueError(f"Unrecognized domain: {domain}")


    elif task == "rec_choice":

        if coi:
            instr = f"Given the request, choose which recommendation is the most suitable. Think step by step. First understand the given image(s) in detail, including its content, style, and vibe. Then, carefully inspect each choice. Recall its content and see if it captures the essence of the image(s). Select the item that best captures this essence. Choose a single item. Don't say anything else."
        else:
            instr = f"Given the request, choose which recommendation is the most suitable. Choose a single item. Don't say anything else."

        return instr

    else:
        raise ValueError(f"Unrecognized task: {task}")

    return instr + '\n'